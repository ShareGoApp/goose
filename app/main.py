from tslearn.metrics import dtw
from loguru import logger
from datetime import datetime
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

# models
# from models.messages import MatchRequest
# from models.messages import GeoRequest
from models.messages import SaveRequest

# logger configuration
logger.add("logs/goose_{time}.log", rotation="12:00", compression="zip", enqueue=True)

# services instances
mongo = MongoService(db=db, logger=logger)
redis = RedisService(client=redis_conn)


# Handles incoming req. for geo driver limitin
async def handle_geo_request(message):
    pid = message["passenger_id"]
    logger.info(f"handling geo-lookup request for: {pid}")

    # get suitable drivers
    docd = await mongo.get_drivers_in_range(pid)

    # push request for matching
    await redis.push_match_request(
        {
            "passenger_id": pid,
            "driver_ids": docd,
        }
    )


# Handles incoming request for DTW compute
async def handle_match_request(message):
    pid = message["passenger_id"]
    logger.info(f"handling match request for: {pid}")

    # get passenger from message
    doc = await mongo.get_passenger(pid)
    doc_nd = geojson_to_ndarray(doc, logger)

    # get drivers from message
    drivers = await mongo.get_driver_list(message["driver_ids"])
    drivers_nd = [geojson_to_ndarray(driver, logger) for driver in drivers]

    # compute dtw from driver list
    results = [dtw(doc_nd, driver) for driver in drivers_nd]

    # todo: find the ride ID of the min driver


    await redis.push_save_reqest({
            "passenger_id": pid,
            "driver_id": "661fc59bbc83e7536732d788", # todo: change hardcoded
            "min_err": min(results),
        })


# Handles incoming req. for geo driver limitin
async def handle_save_request(message):
    pid = message["passenger_id"]
    logger.info(f"handling save request for: {pid}")

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
    result = db.sample_matches.insert_one(document)

    if not result:
        logger.warning("was not able to create match result")


# Redis Pub/Sub Message Listener
async def listener(channel):
    async for message in channel.listen():
        if message["type"] == "message":
            msg_type, data = destructure_message(message)

            if msg_type == "mat_request":
                await handle_match_request(data)
            elif msg_type == "geo_request":
                await handle_geo_request(data)
            elif msg_type == "sav_request":
                await handle_save_request(data)
            else:
                logger.warning("unknown message received")


async def main():
    # boot message
    logger.success("goose is getting up and flying 🪿")

    # subscribe to main channel
    pubsub = redis_conn.pubsub()
    await pubsub.subscribe("main")

    # start listener
    await asyncio.gather(listener(pubsub))


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.close()
