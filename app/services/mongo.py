from bson import ObjectId

# utils
from utils.format import geojson_to_ndarray

class MongoService:
    def __init__(self, db, logger):
        self.db = db
        self.collection = db["sample_rides"]
        self.logger = logger
    
    # method to query a specific passenger
    async def get_passenger(self, id):
        document_id = ObjectId(id)

        # Query for the document by its _id field
        document = self.collection.find_one({"_id": document_id})

        if document:
            return document
        else:
            self.logger.error("no document found")

    # method to query a list of drivers
    async def get_drivers(self, ids):
        # convert str list -> bson list
        id_objects = [ObjectId(id) for id in ids]

        # query in collection
        result = self.collection.find({"_id": {"$in": id_objects}})

        if result:
            return result
        else:
            self.logger.warning("couldn't find documents")
        

    
    async def get_drivers_in_range(self, id):
        # Query for the document by its _id field
        document = self.collection.find_one({"_id": id})

        if document:
            return document
        
        start_lng = -73.987974
        start_lat = 40.747776
        max_dist  = 500

        # Query documents where the start position is 
        # within the specified distance from the reference point
        query = {
            "features.geometry.coordinates": {
                "$geoWithin": {
                    "$centerSphere": [[start_lng, start_lat], max_dist / 6378137.0]
                }
            }
        }

        # Perform the query
        result = self.collection.find(query)

        if result:
            return []
              
        return []

