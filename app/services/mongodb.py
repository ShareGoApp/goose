from loguru import logger
from bson import ObjectId
from uuid import UUID
from datetime import datetime
import json

# models
from models.ride_match import RideMatch


class MongoService:
    def __init__(self, db, logger):
        self.db = db

    # query a specific passenger
    async def get_passenger(self, id):
        try: 
            document_id = ObjectId(id)
            document = self.db["users"].find_one({"_id": document_id})

            if document:
                return document
            else:
                logger.error(f"no passenger found for: {id}")
        except:
            logger.error("failed")

    # query for a specific ride
    async def get_ride(self, id: str):
        try:
            uuid_id = UUID(id)
            document = self.db.rides.find_one({"_id": uuid_id})

            if not document:
                logger.warning(f"no ride found for: {id}")
                return
            
            return document
        except Exception as e:
            logger.error(e)
            logger.error(f"exception caught while retrieving ride: {id}")

        
    async def get_in_timeframe(self, min: datetime, max: datetime):
        # Construct the query to find rides within the specified range
        query = {"departure": {"$gte": min, "$lte": max}}

        # Perform the query
        results = self.db.ride_searches.find(query)

        return self.db.ride_searches.find(query)

        if results:
            logger.warning(f"No ride requested between: {min.isoformat()}")


    # [pubsub] Handles incoming req. for match creation
    async def create_match(self, match_tuple: tuple):
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
        result = self.db.matches.insert_one(document)

        if result:
            msg = f"successfully created match: {result['inserted_id']}"
            serialized_msg = json.dumps(msg)
            logger.success(f"[match]: {msg}")
            return serialized_msg
        else:
            msg = f"failed to create match: {match_tuple[3]}"
            logger.success(f"[match]: {msg}")
            return None
        


    # ================= DEPRECATED =======================


    # query a list of drivers by id
    async def get_driver_list(self, ids):
        id_objects = [ObjectId(id) for id in ids]
        result = self.collection.find({"_id": {"$in": id_objects}})

        if result:
            return result
        else:
            logger.warning("couldn't find documents")

    # find drivers with start locations in range
    async def get_drivers_in_range(self, id):
        # Query for the document by its _id field
        document = self.collection.find_one({"_id": id})

        if document:
            return document

        # need to find the start position of the document.
        start_lng = -73.987974
        start_lat = 40.747776
        max_dist = 500

        # Query documents within the specified distance from the reference point
        query = {
            "_id": {"$ne": ObjectId(id)},  # Exclude document with the specified _id
            "features.geometry.coordinates": {"$geoWithin": {"$centerSphere": [[start_lng, start_lat], max_dist / 6378137.0]}},
        }

        # Perform the query
        cursor = self.collection.find(query)

        if cursor:
            list_ids = [str(doc["_id"]) for doc in cursor]
            return list_ids

        return []
