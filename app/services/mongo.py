from bson import ObjectId

class MongoService:
    def __init__(self, db, logger):
        self.db = db
        self.collection = db["sample_rides"]
        self.logger = logger

    def hello(id):
        return "hello"
    
    async def get_passenger(self, id):
        document_id = ObjectId(id)  # Replace "your_document_id" with the ObjectId of your document

        # Query for the document by its _id field
        document = self.collection.find_one({"_id": document_id})

        if document:
            return document
        else:
            self.logger.error("no document found")

    
    async def get_drivers_in_range(self, id):
        # Define the point near which you want to find locations
        query_point = {"type": "Point", "coordinates": [-73.965364, 40.782865]}

        # Perform the geospatial query
        result = self.collection.find(
            {"location": {"$nearSphere": {"$geometry": query_point}}},
            {"name": 1}  # Projection to include only the 'name' field in the result
        )

        # Iterate over the result and print matching locations
        for location in result:
            self.logger.info(location)

        return result
