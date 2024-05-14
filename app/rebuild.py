# runtime imports
from datetime import datetime, timedelta
from loguru import logger
import asyncio

# database imports
from database.mongodb import database as db
from database.redis import client as rdb

# services
from services.mongo import MongoService # todo: rename file to mongodb
from services.redis import RedisService # todo: hide ugly sortedset, key queries

# models
from models.ride import Ride
from models.ride_request import RideRequest
from models.ride_match import RideMatch

# utils: redis pubsub helpers
from utils.publish import geo_publish
from utils.publish import mat_publish
from utils.publish import sav_publish

# utils: data conversion and format
from utils.format import geojson_to_ndarray
from utils.format import geojson_to_df
from utils.format import destructure_message
from utils.format import map_distance

# utils: geographical computations
from utils.geo import haversine

# logger configuration
logger.add("logs/ext_goose_{time}.log", rotation="12:00", compression="zip", enqueue=True)

# service iniatlizations
mongodb_service = MongoService(db, logger)
# redis_service = RedisService(rdb, logger)

# ========== RETRY HANDLING ==============

# [retry]: retry non-expired rides or remove
async def process_pending(id, score):
    id = id.decode()
    if score <= datetime.now().timestamp():
        # Request has expired, remove it from the queue
        logger.info(f"Removing expired empty ride: {id}")
        await rdb.zrem("empty_rides", id)
    else:
        # Retry unhandled ride
        logger.info(f"Retrying empty ride: {id}")
        await geo_publish({"id": id}) # todo: geo publish is not used anymore


# [retry] retry empty ride with highest priority
async def retry_pending(interval=900):
    while True:
        # pull pending passenger requests sorted by score
        pending = await rdb.zrange("empty_rides", 0, -1, withscores=True)
        for id, score in pending:
            await process_pending(id, score)
        await asyncio.sleep(interval)


# [retry] Add ride to redis sorted set with timestamp as score
async def enqueue_empty_ride(id):
    expiration_date = datetime.now() + timedelta(hours=24)
    score = datetime.timestamp(expiration_date)
    await rdb.zadd("empty_rides", {id: score})


# ========== ALGORITHM HANDLERS ================


async def handle_temporal(message):
    ride = mongodb_service.get_ride(message["id"])

    # Define the range for the query (e.g., 2 hours before and after the datetime)
    delta_time = 180 # TODO: change from hardcoded

    delta_prev = ride["departure"] - timedelta(minutes=delta_time)
    delta_next = ride["departure"] + timedelta(minutes=delta_time)

    # Construct the query to find rides within the specified range
    query = {"departure": {"$gte": delta_prev, "$lte": delta_next}}

    # Perform the query
    results = db["ride_searches"].find(query)

    if not results:
        logger.warning("[temporal]: could not ind any passengers in timeframe")
        return
    
    candidates = []
    for document in results:
        candidates.append(document)
    
    # serialize document to json
    m = Ride(**document)
    serialized = m.model_dump_json()

    # store results in KV-store
    await rdb.json().set("ride", ".", serialized)   # todo: could use ride ID as key to prevent RW-locks
    # rdb.lpush('passengers', *passengers)          # todo: find out what to do here
    

async def handle_spatial(message):
    # retrieve previous results
    ride = await rdb.json().get("ride")
    candidates = await rdb.json().get("candidates")

    d_deviation = ride["max_deviation"] / 1000     # todo: stored in M, haversine expexts KM
    d_route = ride["route"]["shape"]["coordinates"]

    # create indexes
    in_range_start = []
    in_range_dest  = []


    # iterate over driver geo points for start candidates
    for d_point in d_route:
        # check each passengers starting point
        for p in candidates:
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
    on_route = [p for p in in_range_start if p in in_range_dest]

async def handle_correlation(message):
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
    temp = {}

    # populate match
    temp["similarity"]   = match_tuple[0]
    temp["passenger_id"] = match_tuple[1]
    temp["search_id"]    = match_tuple[2]
    temp["ride_id"]      = match_tuple[3]
    temp["seen"]         = False
    temp["created_at"]   = datetime.now()

    # Validate and create a Report instance
    populated = RideMatch(**temp)

    # Insert report into the database
    document = populated.model_dump(by_alias=True, exclude=["id"])
    result = db.matches.insert_one(document)

    if not result:
        logger.warning("task failed to store match document in mongodb")


# [pubsub] Redis Pub/Sub Message Listener
async def listener(channel):
    async for message in channel.listen():
        if message["type"] == "message":
            msg_type, data = destructure_message(message)
            match msg_type:
                case "tem_request": await handle_temporal(data)
                case "spa_request": await handle_spatial(data)
                case "cor_request": await handle_correlation(data)
                case _: logger.warning("unknown message received")


async def main():
    # boot message
    logger.success("goose is getting up and flying 🪿")

    # subscribe to main channel
    pubsub = rdb.pubsub()
    await pubsub.subscribe("main")

    # create tasks from coroutines
    task_listen = asyncio.create_task(listener(pubsub))
    #task_retry = asyncio.create_task(retry_pending)

    # execute asyncio tasks
    await asyncio.gather(task_listen)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.close()
