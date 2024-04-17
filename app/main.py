from tslearn.metrics import dtw
from dotenv import load_dotenv
from datetime import datetime
from loguru import logger
import numpy as np
import asyncio
import math
import json

load_dotenv()  # take environment variables from .env.

# database
from database.redis import client as redisc
from database.mongodb import client as mongoc

# services
# from services.reddit import Reddit
from services.mongo import MongoService

from services.converter import Converter

mongo = MongoService(mongoc)


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

    # Subscribe to main channel
    pubsub = redisc.pubsub()
    await pubsub.subscribe("main")

    # Start listener
    await asyncio.gather(listener(pubsub))


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.close()
