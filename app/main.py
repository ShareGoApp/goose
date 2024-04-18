from tslearn.metrics import dtw
from loguru import logger

# from rq import Queue, Worker
import asyncio
import json, math

# database
from database.redis import client as redis_conn
from database.mongodb import database as db

# services
from services.mongo import MongoService

# utils
from utils.format import geojson_to_ndarray
from utils.compute import get_min_err

# models
from models.messages import MatchRequest
from models.messages import GeoRequest

# logger configuration
logger.add("logs/goose_{time}.log", rotation="12:00", compression="zip", enqueue=True)

# services instances
mongo = MongoService(db=db, logger=logger)


# Handles incoming request for DTW compute
async def handle_match_request(message):

    message.id  # js
    message["id"]  # python

    # get passenger from message
    doc = await mongo.get_passenger(message["passenger_id"])
    doc_nd = geojson_to_ndarray(doc, logger)

    # get drivers from message
    drivers = await mongo.get_drivers(message["driver_ids"])
    drivers_nd = [geojson_to_ndarray(driver, logger) for driver in drivers]

    # compute dtw from driver list
    results = [dtw(doc_nd, driver) for driver in drivers_nd]

    return min(results)


# Hadnles incoming req. for geo driver limiting
async def handle_geo_request(message):
    # get passenger from message
    passenger_id = message["passenger_id"]
    document = await mongo.get_passenger(passenger_id)
    document_nd = geojson_to_ndarray(document, logger)
    pass


# Redis Pub/Sub Message Listener
@logger.catch
async def listener(channel):
    async for message in channel.listen():
        if message["type"] == "message":
            try:
                message = message["data"].decode("UTF-8")
                message = json.loads(message)

                if MatchRequest(**message):
                    await handle_match_request(message)
                elif GeoRequest(**message):
                    await handle_geo_request(message)
                else:
                    logger.warning("unknown message received")

            except:
                logger.warning("malfored message")


async def main():
    # boot message
    logger.success("goose is getting up and flying")

    # subscribe to main channel
    pubsub = redis_conn.pubsub()
    await pubsub.subscribe("main")

    # demo message
    message = json.dumps(
        {
            "type": "match_request",
            "passenger_id": "661fc362bc83e7536732d787",
            "driver_ids": ["661fc59bbc83e7536732d788", "661fc5c0bc83e7536732d789"],
        }
    )

    await redis_conn.publish("main", message)

    # start listener
    await asyncio.gather(listener(pubsub))


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.close()
