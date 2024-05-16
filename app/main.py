# runtime imports
from datetime import datetime, timedelta
from tslearn.metrics import dtw
from loguru import logger
import asyncio, heapq, json

# database imports
from database.mongodb import database as db
from database.redis import client as rdb

# services
from services.mongodb import MongoService # todo: rename file to mongodb
from services.redis import RedisService # todo: hide ugly sortedset, key queries

# models
from models.ride import Ride
from models.ride_request import RideRequest
from models.ride_search import RideSearch
from models.ride_match import RideMatch

# utils: data conversion and format
from utils.format import geojson_to_df
from utils.format import destructure_message

# utils: geographical computations
from utils.geo import haversine

# logger configuration
logger.add("logs/ext_goose_{time}.log", rotation="12:00", compression="zip", enqueue=True)

# service iniatlizations
mongodb_service = MongoService(db, logger)
redis_service = RedisService(rdb)

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
        await rdb.publish("main", f"tem_request:{id}")


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


# ============== REDIS HELPER ==================

async def get_from_cache(id):
    # retrieve previous results
    ride_serialized = await rdb.json().get(id, ".ride")
    ride = Ride.model_validate_json(ride_serialized).model_dump()

    # retieve candidates
    candidates_serialized = await rdb.json().get(id, ".candidates")
    candidates_models = [RideSearch.model_validate_json(doc) for doc in candidates_serialized]
    candidates = [doc.model_dump() for doc in candidates_models]

    return ride, candidates


# ========== ALGORITHM HANDLERS ================


async def handle_temporal(id: str):
    # query ride to match by id
    ride = await mongodb_service.get_ride(id)
    ride_serialized = Ride(**ride).model_dump_json()

    if not ride:
        logger.warning("[temporal]: not able to retrieve ride: {id}")
        return

    # Define the range for the query
    delta_time = 180                                                # todo: should exists on ride document
    delta_prev = ride["departure"] - timedelta(minutes=delta_time)
    delta_next = ride["departure"] + timedelta(minutes=delta_time)

    # perform the query to find rides within the specified range
    results = await mongodb_service.get_in_timeframe(delta_prev, delta_next)

    # build candidate list
    candidates = []
    for document in results:
        logger.success(f"[temporal]: added {str(document['_id'])} to candidate list")
        candidates.append(document)
    
    if len(candidates) == 0:
        await enqueue_empty_ride(id)
        logger.warning("[temporal]: candidate list is empty")
        return
    
    try:
        candidates_serialized = [RideSearch(**doc).model_dump_json() for doc in candidates]
    except:
        logger.error(f"[temporal]: failed to serialize candidates")
        return

    # store results in KV-store
    await rdb.json().set(id, ".", {})                                   # create object root
    await rdb.json().set(id, ".ride", ride_serialized)                  # store ride request for reuse
    await rdb.json().set(id, ".candidates", candidates_serialized)      # store list of initial candidates
    await rdb.publish("main", f"spa_request:{id}")                      # message start spatial analysis
    

async def handle_spatial(id: str):
    # todo: this could props be optimized
    ride, candidates = await get_from_cache(id)

    d_deviation = ride["max_deviation"] / 1000     # todo: stored in M, haversine expexts KM
    d_route = ride["route"]["shape"]["coordinates"]

    # create subsets
    in_range_start = []
    in_range_dest  = []

    # compute accepted pick-ups from candidates
    for d_point in d_route:
        for candidate in candidates:
            # check each passengers starting point
            p_points = candidate["route"]["shape"]["coordinates"]
            dist = haversine(d_point[0], d_point[1], p_points[0][0], p_points[0][1])

            # check if candidate is within threshhold
            if dist <= d_deviation:
                if candidate not in in_range_start:
                    logger.success(f"[spatial]: added {str(candidate['id'])} to candidate start list")
                    in_range_start.append(candidate)

    # compute accepted drop-offs from in_range_start
    for d_point in d_route:
        for candidate in in_range_start:
            # check passengers that passed start check
            p_points = candidate["route"]["shape"]["coordinates"]
            dist = haversine(d_point[0], d_point[1], p_points[-1][0], p_points[-1][1])

            # check if candidate is within threshhold
            if dist <= d_deviation:
                if candidate not in in_range_dest:
                    logger.success(f"[spatial]: added {str(candidate['id'])} to candidate destination list")
                    in_range_dest.append(candidate)

    # common elements from lists compose candidates subset
    on_route = [p for p in in_range_start if p in in_range_dest]

    if len(on_route) == 0:
        await enqueue_empty_ride(id)
        return
    
    # serialize objects
    on_route_serialized = [RideSearch(**doc).model_dump_json() for doc in on_route]

    # store results in KV-store
    await rdb.json().set(id, ".candidates", on_route_serialized)    # store list of revised candidates
    await rdb.publish("main", f"cor_request:{id}")                 # message start route correlation analysis


async def handle_correlation(id: str):
    ride, candidates = await get_from_cache(id)

    # load route into a pandas dataframe
    df_ride = geojson_to_df(ride)

    short_list = []
    for c in candidates:
        print(c) #nocheckin
        df_candidate = geojson_to_df(c)
        distance = dtw(df_ride, df_candidate)              # compute err with dynamic-time warping
        match_tuple = (distance, c["passenger"], c["id"], ride["id"])
        short_list.append(match_tuple)
        logger.success(f'[correlation] found new match: {match_tuple}')
    
    heapq.heapify(short_list)                              # in-place convert list to heap-queue
    for _ in range(ride["seats_available"]):
        match_tuple = heapq.heappop(short_list)            # retrieve elem with lowest err
        await mongodb_service.create_match(match_tuple)    # create the match in database
        

# [pubsub] Redis Pub/Sub Message Listener
async def listener(channel):
    async for message in channel.listen():
        if message["type"] == "message":
            msg_type, id = destructure_message(message)
            match msg_type:
                case "tem_request": await handle_temporal(id)
                case "spa_request": await handle_spatial(id)
                case "cor_request": await handle_correlation(id)
                case _: logger.warning("unknown message received")


async def main():
    # boot message
    logger.success("goose is getting up and flying 🪿")

    # subscribe to main channel
    pubsub = rdb.pubsub()
    await pubsub.subscribe("main")

    # create tasks from coroutines
    task_listen = asyncio.create_task(listener(pubsub))
    task_retry = asyncio.create_task(retry_pending())

    # execute asyncio tasks
    await asyncio.gather(task_listen)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.close()
