from datetime import datetime, timedelta
from tslearn.metrics import dtw
from loguru import logger
import asyncio


# database
from database.redis import client as redis
from database.mongodb import database as db

# services
from services.mongo import MongoService
# from services.redis import RedisService

# utils
from utils.format import geojson_to_ndarray
from utils.format import destructure_message
from utils.format import map_distance

from utils.publish import geo_publish
from utils.publish import mat_publish
from utils.publish import sav_publish

# models
from models.messages import SaveRequest

# logger configuration
logger.add("logs/goose_{time}.log", rotation="12:00", compression="zip", enqueue=True)

# services instances
mongo = MongoService(db=db, logger=logger)
# redis_service = RedisService(client=redis, logger=logger)


# [redis]
async def process_pending(pid, score):
    pid = pid.decode()
    if score <= datetime.now().timestamp():
        # Request has expired, remove it from the queue
        logger.info(f"Removing expired unmatched passenger: {pid}")
        await redis.zrem("unmatched_passengers", pid)
    else:
        # Retry unmatched passenger
        logger.info(f"Retrying unmatched passenger: {pid}")
        await geo_publish({"pid": pid, "max_radius": 500}) # FIXME: hardcoded value


# [redis] New coroutine to retry unmatched passengers with higher priority
async def retry_pending(interval=900):
    while True:
        # pull pending passenger requests sorted by score
        pending = await redis.zrange("unmatched_passengers", 0, -1, withscores=True)
        for pid, score in pending:
            await process_pending(pid, score)
        await asyncio.sleep(interval)


# [redis] Add unmatched passenger to Redis sorted set with timestamp as score
async def enqueue_unmatched_passenger(pid):
    expiration_date = datetime.now() + timedelta(hours=24)
    score = datetime.timestamp(expiration_date)
    await redis.zadd("unmatched_passengers", {pid: score})


# [pubsub] Handles incoming request for geographical lookups
async def handle_geo_request(message):
    pid = message["pid"]
    logger.info(f"[geo-lookup] handling request for: {pid}")

    # look for drivers in range of departure and destination
    in_departure = await mongo.get_drivers_in_range(pid) 
    # in_destination = await mongo.get_drivers_in_range(pid)

    # compute the common drivers from near departure and near destination
    # docd = [driver for driver in in_departure if driver in in_destination]

    if len(in_departure) > 0: 
        # await mat_publish({"pid": pid, "driver_ids": docd})
        await mat_publish({"pid": pid, "driver_ids": in_departure})
    else:
        logger.warning("[save]: couldn't find any drivers in range")
        await enqueue_unmatched_passenger(pid)


# [pubsub] Handles incoming request for DTW compute
async def handle_match_request(message):
    pid = message["pid"]
    logger.info(f"[match]: handling request for: {pid}")

    # get passenger from message
    doc = await mongo.get_passenger(pid)
    doc_nd = geojson_to_ndarray(doc)
    
    # get drivers from message
    drivers = await mongo.get_driver_list(message["driver_ids"])

    # compute dtw from driver list
    results = [map_distance(doc_nd, driver) for driver in drivers]
    optimal = min(results, key=lambda x: x["dist"]) if len(results) > 0 else {}

    if optimal:
        await sav_publish({
            "pid": pid, 
            "driver_id": str(optimal["id"]), 
            "min_err": optimal["dist"]
            })
    else:
        logger.warning("[match] was not able to compute a match")


# [pubsub] Handles incoming req. for geo driver limitin
async def handle_save_request(message):
    pid = message["pid"]
    logger.info(f"[save] handling request for: {pid}")

    # Convert partial response body to dict
    dict = {}

    # Add metadata
    dict["created_at"] = datetime.now()

    # Add empty lists for content
    dict["passenger_id"] = message["pid"]
    dict["driver_id"] = message["driver_id"]
    dict["min_err"] = message["min_err"]

    # Validate and create a Report instance
    final_dict = SaveRequest(**dict)

    # Insert report into the database
    document = final_dict.model_dump(by_alias=True, exclude=["id"])
    result = db.matches.insert_one(document)

    if not result:
        logger.warning("was not able to create match result")


# [pubsub] Redis Pub/Sub Message Listener
async def listener(channel):
    async for message in channel.listen():
        if message["type"] == "message":
            msg_type, data = destructure_message(message)
            match msg_type:
                case "mat_request": await handle_match_request(data)
                case "geo_request": await handle_geo_request(data)
                case "sav_request": await handle_save_request(data)
                case _: logger.warning("unknown message received")


async def main():
    # boot message
    logger.success("goose is getting up and flying 🪿")

    # subscribe to main channel
    pubsub = redis.pubsub()
    await pubsub.subscribe("main")

    # create tasks from coroutines
    task_listen = asyncio.create_task(listener(pubsub))
    task_retry = asyncio.create_task(retry_pending())

    # start listener
    await asyncio.gather(task_listen,task_retry)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.close()
