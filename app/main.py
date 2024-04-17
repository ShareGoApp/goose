from tslearn.metrics import dtw
from dotenv import load_dotenv
from datetime import datetime
from loguru import logger
import numpy as np
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
from utils.data import geojson_to_matrix
from utils.data import matrix_to_geojson

# logger configuration
logger.add("logs/{time}.log", rotation="12:00", compression="zip", enqueue=True)


# load sample data
with open("app/data/passenger.json", "r") as file:
    drivers = json.load(file)

with open("app/data/drivers.json", "r") as file:
    passengers = json.load(file)


# demo
def get_passenger_by_id(id):
    for p in passengers:
        if p["id"] == id:
            return p


# demo
def get_driver_by_id(id):
    for d in drivers:
        if d["id"] == id:
            return d
    return None


def get_min_error_driver(p_data):
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
    async for message in channel.listen():
        if message["type"] == "message":
            request = message["data"].decode("UTF-8")
            p = get_passenger_by_id(request)
            logger.info(p)

            p_converted = Converter.convert_data(p["data"])
            logger.info(p_converted)

            m_dist = get_min_error_driver(p["data"])
            logger.info(m_dist)

            # try:
            #     distance = dtw(data_fmt, driver1_fmt)
            #     logger.success(distance)
            # except:
            #     logger.error("failed to compute dtw")


async def main():
    # Info dump
    logger.success("server started")

    # TODO: remove test code
    mongo = MongoService(db, logger)
    converter = Converter(logger)

    # passenger
    doc_p = await mongo.get_passenger("661fc362bc83e7536732d787")
    doc_p_m = geojson_to_matrix(doc_p)
    doc_p_nd = converter.convert_data(doc_p_m)

    # driver
    doc_d = await mongo.get_passenger("661fc5c0bc83e7536732d789")
    doc_d_m = geojson_to_matrix(doc_d)
    doc_d_nd = converter.convert_data(doc_d_m)

    # test logging
    logger.info(doc_p_nd)
    logger.info(doc_d_nd)

    # compute drift
    distance = dtw(doc_p_nd, doc_d_nd)
    logger.success(distance)

    # Subscribe to main channel
    pubsub = redisc.pubsub()
    await pubsub.subscribe("main")

    # Start listener
    await asyncio.gather(listener(pubsub))


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.close()
