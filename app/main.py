from tslearn.metrics import dtw
from loguru import logger
import asyncio
import math
import json

# database
from database.redis import client as redisc
from database.mongodb import database as db

# services
from services.mongo import MongoService
from services.converter import Converter

# utils
from utils.format import geojson_to_ndarray

# logger configuration
logger.add("logs/goose_{time}.log", rotation="12:00", compression="zip", enqueue=True)

# FIXME: not sure if this should be located here
def get_min_error_driver(p_data, drivers):
    min_driver = math.inf

    for d in drivers:
        d_data = Converter.convert_data(d["data"])
        dist = dtw(p_data, d_data)
        if dist < min_driver:
            min_driver = dist

    return min_driver


# Redis Pub/Sub Message Listener
@logger.catch
async def listener(channel):
    # init services
    mongo = MongoService(db, logger)

    doc_one = await mongo.get_passenger("661fc59bbc83e7536732d788")
    doc1_nd = geojson_to_ndarray(doc_one)

    doc_two = await mongo.get_passenger("661fc5c0bc83e7536732d789")
    doc2_nd = geojson_to_ndarray(doc_two)

    async for message in channel.listen():
        if message["type"] == "message":
            request = message["data"].decode("UTF-8")
            p = await mongo.get_passenger(request)
            p_nd = geojson_to_ndarray(p)
            
            # compute dist for 1
            dist_one = dtw(p_nd, doc1_nd)
            logger.info(dist_one)

            # compute dist for 2
            dist_two = dtw(p_nd, doc2_nd)
            logger.info(dist_two)

            # return min dist
            logger.success(f"found min err: {min(dist_one, dist_two)}")


async def main():
    # Info dump
    logger.success("server started")

    # Subscribe to main channel
    pubsub = redisc.pubsub()
    await pubsub.subscribe("main")

    # Start listener
    await asyncio.gather(listener(pubsub))


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.close()
