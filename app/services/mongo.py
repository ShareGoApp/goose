from bson import ObjectId


class MongoService:
    def __init__(self, db, logger):
        self.db = db
        self.collection = db["rides"]  # todo: change hardcoded
        self.logger = logger

    # query a specific passenger
    async def get_passenger(self, id):
        document_id = ObjectId(id)
        document = self.collection.find_one({"_id": document_id})

        if document:
            return document
        else:
            self.logger.error("no document found")

    # query a list of drivers by id
    async def get_driver_list(self, ids):
        id_objects = [ObjectId(id) for id in ids]
        result = self.collection.find({"_id": {"$in": id_objects}})

        if result:
            return result
        else:
            self.logger.warning("couldn't find documents")

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

        #if cursor:
        #    list_ids = [str(doc["_id"]) for doc in cursor]
        #    return list_ids

        return []

    # save a new document for match
    async def create_match_document(self, id):
        pass
