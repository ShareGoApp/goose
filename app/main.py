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
    ride = await rdb.json().get(id, ".ride")

    # retieve candidates
    candidates = await rdb.json().get(id, ".candidates")
    # candidates_models = [RideSearch.model_validate_json(doc) for doc in candidates]
    # candidates = [doc.model_dump() for doc in candidates_models]

    return ride, candidates


# ========== ALGORITHM HANDLERS ================


async def handle_temporal(id: str):

    # query ride to match by id
    ride = await mongodb_service.get_ride(id)

    if not ride:
        logger.warning("[temporal]: not able to retrieve ride: {id}")
        return
    
    # serialize document to dictionary
    ride_serialized = Ride(**ride).model_dump(mode="json", by_alias=True)

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
        candidates_serialized = [RideSearch(**doc).model_dump(mode="json", by_alias=True) for doc in candidates]
    except:
        logger.error(f"[temporal]: failed to serialize candidates")
        return

    # store results in KV-store
    await rdb.json().set(id, ".", {})                                   # create object root
    await rdb.json().set(id, ".ride", ride_serialized)                  # store ride request for reuse
    await rdb.json().set(id, ".candidates", candidates_serialized)      # store list of initial candidates
    await rdb.publish("main", f"spa_request:{id}")                       # message start spatial analysis
    

async def handle_spatial(id: str):
    logger.info(id)

    # todo: this could props be optimized
    ride, candidates = await get_from_cache(id)

    d_deviation = ride["max_deviation"] / 1000     # todo: stored in M, haversine expexts KM
    d_route = ride["route"]["shape"]["coordinates"]

    # create subsets
    in_range_start = []
    in_range_start_added = set()

    in_range_dest  = []
    in_range_dest_added = set()

    # compute accepted pick-ups from candidates 
    for index, d_point in enumerate(d_route):
        for candidate in candidates:
            # check each passengers starting point
            c_points = candidate["route"]["shape"]["coordinates"]
            dist = haversine(d_point[0], d_point[1], c_points[0][0], c_points[0][1])

            # check if candidate is within threshhold
            if dist <= d_deviation:
                if candidate['_id'] not in in_range_start_added:
                    logger.success(f"[spatial]: added {str(candidate['_id'])}, found at: {index}, to candidate start list")
                    in_range_start.append((candidate, index))
                    in_range_start_added.add(candidate['_id'])
                else:
                    logger.info(f"[spatial]: skipped {str(candidate['_id'])}, found at: {index}")

    # compute accepted drop-offs from in_range_start
    for index, d_point in enumerate(d_route):
        for (candidate, index) in in_range_start:
           # check passengers that passed start check
            c_points = candidate["route"]["shape"]["coordinates"]
            dist = haversine(d_point[0], d_point[1], c_points[-1][0], c_points[-1][1])

            # check if candidate is within threshhold
            if dist <= d_deviation:
                if candidate['_id'] not in in_range_dest_added:
                    logger.success(f"[spatial]: added {str(candidate['_id'])}, found at: {index}, to candidate destination list")
                    in_range_dest.append((candidate, index))
                    in_range_dest_added.add(candidate['_id'])
                else:
                    logger.info(f"[spatial]: skipped {str(candidate['_id'])}, found at: {index}")

    # check for same direction
    on_route = []
    for (candidate_s, index_s) in in_range_start:
        if any(candidate_s['_id'] == candidate_d['_id'] for (candidate_d, _)  in in_range_dest):
            logger.success(f"[spatial]: found common element: {candidate_s['_id']}, si: {index_s}")
            on_route.append(candidate_s['_id'])

    logger.info(in_range_start_added)
    logger.info(in_range_dest_added)
    logger.info(on_route)

    # common elements from lists compose candidates subset
    on_route = [p for p in in_range_start if p in in_range_dest]

    if len(on_route) == 0:
         await enqueue_empty_ride(id)
         return
    
    # serialize objects
    on_route_serialized = [RideSearch(**doc).model_dump(mode="json", by_alias=True) for (doc, _) in on_route]

    # store results in KV-store
    await rdb.json().set(id, ".candidates", on_route_serialized)    # store list of revised candidates
    await rdb.publish("main", f"cor_request:{id}")                  # message start route correlation analysis


# ================ VARIATION SPATIAL ================

# optimization of about function without redis operations
async def compute_candidates_within_range(ride_id):
    ride, candidates = await get_from_cache(ride_id)

    deviation = ride["max_deviation"] / 1000  # deviation in km
    route = ride["route"]["shape"]["coordinates"]

    in_range_start = set()
    in_range_dest = set()

    for candidate in candidates:
        ps = candidate["route"]["shape"]["coordinates"][0]
        pe = candidate["route"]["shape"]["coordinates"][-1]

        start_in_range = any(haversine(rp[0], rp[1], ps[0], pe[1]) <= deviation for rp in route)
        if start_in_range:
            in_range_start.add(candidate['_id'])

        end_in_range = any(haversine(rp[0], rp[1], pe[0], pe[1]) <= deviation for rp in route)
        if end_in_range:
            in_range_dest.add(candidate['_id'])

    on_route_ids = in_range_start.intersection(in_range_dest)
    on_route_candidates = [candidate for candidate in candidates if candidate['_id'] in on_route_ids]

    return on_route_candidates


# optimization that includes order of occurence of start and destination
async def compute_candidates_within_range(ride_id):
    ride, candidates = await get_from_cache(ride_id)

    d_deviation = ride["max_deviation"] / 1000  # deviation in km
    d_route = ride["route"]["shape"]["coordinates"]

    def find_point_in_route(route, point, deviation):
        for index, d_point in enumerate(route):
            if haversine(d_point[0], d_point[1], point[0], point[1]) <= deviation:
                return index
        return -1

    on_route_candidates = []

    for candidate in candidates:
        p_start = candidate["route"]["shape"]["coordinates"][0]
        p_end = candidate["route"]["shape"]["coordinates"][-1]

        start_index = find_point_in_route(d_route, p_start, d_deviation)
        end_index = find_point_in_route(d_route, p_end, d_deviation)

        if start_index != -1 and end_index != -1 and start_index < end_index:
            on_route_candidates.append(candidate)
            logger.success(f"[spatial]: added {str(candidate['_id'])} to candidate list")

    return on_route_candidates


# ================ VARIATION SPATIAL END ================

async def handle_correlation(id: str):    
    ride, candidates = await get_from_cache(id)

    # load route into a pandas dataframe
    df_ride = geojson_to_df(ride)

    short_list = []
    for c in candidates:
        print(c) #nocheckin
        df_candidate = geojson_to_df(c)
        distance = dtw(df_ride, df_candidate)              # compute err with dynamic-time warping
        match_tuple = (distance, c["passenger"], c['_id'], ride['_id'])
        short_list.append(match_tuple)
        logger.success(f'[correlation] found new match: {match_tuple}')
    
    heapq.heapify(short_list)                              # in-place convert list to heap-queue
    for _ in range(min(ride["seats_available"], len(short_list))):               # todo: should number of matches to create from results
        logger.success("created new match")
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
    await pubsub.subscribe("dev")

    # create tasks from coroutines
    task_listen = asyncio.create_task(listener(pubsub))
    #task_retry  = asyncio.create_task(retry_pending())

    # execute asyncio tasks
    await asyncio.gather(task_listen)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.close()
