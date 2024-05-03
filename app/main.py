from tslearn.metrics import dtw
from datetime import datetime, timedelta
from loguru import logger
import asyncio

# database
from database.redis import client as redis_conn
from database.mongodb import database as db

# services
from services.mongo import MongoService
from services.redis import RedisService

# utils
from utils.format import geojson_to_ndarray
from utils.format import destructure_message
from utils.env import get_variable

# models
# from models.messages import MatchRequest
# from models.messages import GeoRequest
from models.messages import SaveRequest

# logger configuration
logger.add("logs/goose_{time}.log", rotation="12:00", compression="zip", enqueue=True)

# services instances
mongo = MongoService(db=db, logger=logger)
redis = RedisService(client=redis_conn)
retry_interval = int(get_variable("RETRY_INTERVAL")) # TODO: move

def computed_zip(passenger, driver):
    driver_nd = geojson_to_ndarray(driver, logger)
    return {
        "id": driver["_id"],
        "dist": dtw(passenger, driver_nd)
    }


# Add unmatched passenger to Redis sorted set with timestamp as score
async def enqueue_unmatched_passenger(passenger_id):
    expiration_date = datetime.now() + timedelta(hours=24)
    score = datetime.timestamp(expiration_date)
    await redis_conn.zadd("unmatched_passengers", {passenger_id: score})

# todo: unused
async def invalidate_expired_requests(pid, score):
    if score <= datetime.now().timestamp():
        # Request has expired, remove it from the queue
        logger.info(f"Removing expired unmatched passenger: {pid}")
        await redis_conn.zrem("unmatched_passengers", pid)


# New coroutine to retry unmatched passengers with higher priority
async def retry_unmatched_passengers(interval=900):
    while True:
        # Fetch and process unmatched passengers sorted by score (timestamp)
        unmatched_passengers = await redis_conn.zrange("unmatched_passengers", 0, -1, withscores=True)

        # iterate over passenger stored in back queue
        for pid, score in unmatched_passengers:
            pid = pid.decode()
            score = score
            if score <= datetime.now().timestamp():
                # Request has expired, remove it from the queue
                logger.info(f"Removing expired unmatched passenger: {pid}")
                await redis_conn.zrem("unmatched_passengers", pid)
            else:
                # Retry unmatched passenger
                logger.info(f"Retrying unmatched passenger: {pid}")
                await handle_geo_request({"passenger_id": pid})

        await asyncio.sleep(retry_interval)


# Handles incoming req. for geo driver limitin
async def handle_geo_request(message):
    pid = message["passenger_id"]
    logger.info(f"[geo-lookup] handling request for: {pid}")

    # get suitable drivers
    docd = await mongo.get_drivers_in_range(pid)

    if len(docd) > 0: 
        await redis.push_match_request({
                "passenger_id": pid,
                "driver_ids": docd,
            })
    else:
        logger.warning("[save]: couldn't find any drivers in range")
        await enqueue_unmatched_passenger(pid)


# Handles incoming request for DTW compute
async def handle_match_request(message):
    pid = message["passenger_id"]
    logger.info(f"[match] handling request for: {pid}")

    # get passenger from message
    doc = await mongo.get_passenger(pid)
    doc_nd = geojson_to_ndarray(doc, logger)
    
    # get drivers from message
    drivers = await mongo.get_driver_list(message["driver_ids"])

    # compute dtw from driver list
    results = [computed_zip(doc_nd, driver) for driver in drivers]
    optimal = min(results, key=lambda x: x["dist"]) if len(results) > 0 else {}

    if optimal:
        await redis.push_save_reqest({
            "passenger_id": pid,
            "driver_id": str(optimal['id']),
            "min_err": optimal['dist'],
        })
    else:
        logger.warning("[match] was not able to compute a match")


# Handles incoming req. for geo driver limitin
async def handle_save_request(message):
    pid = message["passenger_id"]
    logger.info(f"[save] handling request for: {pid}")

    # Convert partial response body to dict
    dict = {}

    # Add metadata
    dict["created_at"] = datetime.now()

    # Add empty lists for content
    dict["passenger_id"] = message["passenger_id"]
    dict["driver_id"] = message["driver_id"]
    dict["min_err"] = message["min_err"]

    # Validate and create a Report instance
    final_dict = SaveRequest(**dict)

    # Insert report into the database
    document = final_dict.model_dump(by_alias=True, exclude=["id"])
    result = db.matches.insert_one(document)

    if not result:
        logger.warning("was not able to create match result")


# Redis Pub/Sub Message Listener
async def listener(channel):
    async for message in channel.listen():
        if message["type"] == "message":
            msg_type, data = destructure_message(message)

            print(msg_type)
            match msg_type:
                case "mat_request": await handle_match_request(data)
                case "geo_request": await handle_geo_request(data)
                case "sav_request": await handle_save_request(data)
                case _: logger.warning("unknown message received")


async def main():
    # boot message
    logger.success("goose is getting up and flying 🪿")

    # subscribe to main channel
    pubsub = redis_conn.pubsub()
    await pubsub.subscribe("main")

    # Start the retry coroutine
    asyncio.create_task(retry_unmatched_passengers())

    # start listener
    await asyncio.gather(listener(pubsub))


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.close()
