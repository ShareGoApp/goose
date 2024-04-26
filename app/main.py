from tslearn.metrics import dtw
from datetime import datetime
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


# Handles incoming request for DTW compute
async def handle_match_request(message):
    logger.info(f"[match] handling request for: {pid}")

    # get passenger from message
    pid = message["passenger_id"]
    doc = await mongo.get_passenger(pid)
    doc_nd = geojson_to_ndarray(doc, logger)

    def computed_zip(passenger, driver):
        driver_nd = geojson_to_ndarray(driver, logger)
        return {
            "id": driver["_id"],
            "dist": dtw(passenger, driver_nd)
        }
    
    # get drivers from message
    drivers = await mongo.get_driver_list(message["driver_ids"])

    # compute dtw from driver list
    results = [computed_zip(doc_nd, driver) for driver in drivers]
    optimal = min(results, key=lambda x: x["dist"]) if len(results) > 0 else {}

    await redis.push_save_reqest({
        "passenger_id": pid,
        "driver_id": str(optimal['id']),
        "min_err": optimal['dist'],
    })


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

    # start listener
    await asyncio.gather(listener(pubsub))


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.close()
