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
from database.redis import client as redis_client

# services
# from services.reddit import Reddit

# logger configuration
logger.add("logs/{time}.log", rotation="12:00", compression="zip", enqueue=True)


# load sample data
with open("data/drivers.json", "r") as file:
    drivers = json.load(file)

with open("data/passenger.json", "r") as file:
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
        d_data = convert_data(d["data"])
        dist = dtw(p_data, d_data)
        if dist < min_driver:
            min_driver = dist
    
    return min_driver


# convert timestamp strings to unix time
def convert_to_unix(timestamp) -> float:
    try:
        logger.debug("converting to unix")
        datetime_obj = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        unix_time = datetime_obj.timestamp()
        return unix_time
    except:
        return logger.error("failed to convert unix")


# convert json string data to numpy matrices
def convert_data(matrix):
    try:
        # Convert the timestamps to Unix time using pandas (you could also use datetime module in Python)
        timestamps = [convert_to_unix(date) for _, _, date in matrix]

        # Create a numpy array for latitudes, longitudes, and Unix timestamps
        latitudes = np.array([lat for lat, _, _ in matrix])
        longitudes = np.array([lng for _, lng, _ in matrix])
        timestamps = np.array(timestamps)

        logger.success("succesfully converted data")
        return np.array(list(zip(latitudes, longitudes, timestamps)))
    except:
        logger.error("failed to convert data to np matrix")
        return None


# Redis Pub/Sub Message Listener
@logger.catch
async def listener(channel):
    async for message in channel.listen():
        if message["type"] == "message":
            request = message["data"].decode("UTF-8")
            p = get_passenger_by_id(request)
            logger.info(p)

            p_converted = convert_data(p["data"])
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
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("main")

    # Start listener
    await asyncio.gather(listener(pubsub))


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.close()
