from datetime import datetime, timedelta
from tslearn.metrics import dtw
from loguru import logger
import pandas as pd
import asyncio

# new
import heapq


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

from utils.geo import haversine

# models
from models.messages import SaveRequest

# logger configuration
logger.add("logs/goose_{time}.log", rotation="12:00", compression="zip", enqueue=True)

# services instances
mongo = MongoService(db=db, logger=logger)
# redis_service = RedisService(client=redis, logger=logger)


# GLOBALS
driver = {}
passengers = []


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

# =========================== NEW ===========================


async def handle_temporal(message):
    id = message["id"]
    driver = mongo.get_driver(id)

    # Define the range for the query (e.g., 2 hours before and after the datetime)
    delta_time = 180 # TODO: change from hardcoded

    delta_prev = driver["departure"] - timedelta(minutes=delta_time)
    delta_next = driver["departure"] + timedelta(minutes=delta_time)

    # Construct the query to find rides within the specified range
    query = {"departure": {"$gte": delta_prev, "$lte": delta_next}}

    # Perform the query
    results = db["ride_searches"].find(query)

    if not results:
        logger.warning("[temporal]: could not ind any passengers in timeframe")
    else:
        passengers = []
        for document in results:
            passengers.append(document)

        redis.json().set("driver", ".", driver, decode_keys=True)
        redis.lpush('passengers', *passengers)

async def handle_spatial(messages):
    d_deviation = 5 # TODO: could come from driver Haversine takes KM and db is M
    d_route = driver["route"]["shape"]["coordinates"]

    # create indexes
    in_range_start = []
    in_range_dest  = []

    # TODO: optimize please
    # iterate over driver geo points for start candidates
    for d_point in d_route:
        # check each passengers starting point
        for p in passengers:
            p_points = p["route"]["shape"]["coordinates"]
            dist = haversine(d_point[0], d_point[1], p_points[0][0], p_points[0][1])
            if dist <= d_deviation:
                if p not in in_range_start:
                    in_range_start.append(p)

    # iterate over driver geo points for destination candidates
    for d_point in d_route:
        # check passengers that passed start check
        for p in in_range_start:
            p_points = p["route"]["shape"]["coordinates"]
            dist = haversine(d_point[0], d_point[1], p_points[-1][0], p_points[-1][1])
            if dist <= d_deviation:
                if p not in in_range_dest:
                    in_range_dest.append(p)

    # common elements from lists compose candidates subset
    candidates = [p for p in in_range_start if p in in_range_dest]


def geojson_to_df(data) -> pd.DataFrame:
    # Extract passenger data
    coordinates = data["route"]["shape"]["coordinates"]
    # timestamps = [datetime.isoformat(ts) for ts in data["route"]["timestamps"]]

    # Create DataFrame
    df = pd.DataFrame({
        "lat": [coord[1] for coord in coordinates],
        "lon": [coord[0] for coord in coordinates], 
        # "timestamp": pd.to_datetime(timestamps)
    })

    return df

async def handle_correlation(driver):
    df_d = geojson_to_df(driver) # todo: find driver

    short_list = []
    for c in candidates:
        df_c = geojson_to_df(c)
        match_tuple = (dtw(df_d, df_c), c["passenger"], c["_id"], driver["_id"])
        short_list.append(match_tuple)
    
    for s in range(driver["available_seats"]):
        match_tuple = heapq.heappop(short_list)
        await create_match(match_tuple)

# [pubsub] Handles incoming req. for match creation
async def create_match(match_tuple: tuple):
    # Convert partial response body to dict
    dict = {}

    # populate match
    dict["similarity"]   = match_tuple[0]
    dict["passenger_id"] = match_tuple[1]
    dict["search_id"]    = match_tuple[2]
    dict["ride_id"]      = match_tuple[3]
    dict["seen"]         = False
    dict["created_at"]   = datetime.now()

    # Validate and create a Report instance
    populated = SaveRequest(**dict)

    # Insert report into the database
    document = populated.model_dump(by_alias=True, exclude=["id"])
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
