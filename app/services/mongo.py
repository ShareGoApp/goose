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
