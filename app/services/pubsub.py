from loguru import logger
from datetime import datetime

# pydantic models
from models.messages import SaveRequest


class MessageHandler:
    def __init__(self, db, redis):
        self.db = db
        self.redis = redis

    # Handles incoming req. for geo driver limitin
    async def handle_geo_request(self, message):
        pid = message["pid"]
        logger.info(f"[geo-lookup] handling request for: {pid}")

        # get suitable drivers
        docd = await self.db.get_drivers_in_range(pid)

        if len(docd) > 0:
            await self.redis.push_match_request(
                {
                    "pid": pid,
                    "driver_ids": docd,
                }
            )
        else:
            logger.warning("[save]: couldn't find any drivers in range")
            await enqueue_unmatched_passenger(pid)

    # Handles incoming request for DTW compute
    async def handle_match_request(message):
        pid = message["pid"]
        logger.info(f"[match] handling request for: {pid}")

        # get passenger from message
        doc = await mongo.get_passenger(pid)
        doc_nd = geojson_to_ndarray(doc, logger)
        
        # get drivers from message
        drivers = await mongo.get_driver_list(message["driver_ids"])

        # compute dtw from driver list
        results = [computed_zip(doc_nd, driver) for driver in drivers]
        optimal = min(results, key=lambda x: x["dist"]) if len(results) > 0 else {}

        if optimal:
            await redis.push_save_reqest({
                "pid": pid,
                "driver_id": str(optimal['id']),
                "min_err": optimal['dist'],
            })
        else:
            logger.warning("[match] was not able to compute a match")

    # Handles incoming req. for geo driver limitin
    async def handle_save_request(self, message):
        pid = message["pid"]
        logger.info(f"[save] handling request for: {pid}")

        # Convert partial response body to dict
        dict = {}

        # Add metadata
        dict["created_at"] = datetime.now()

        # Add empty lists for content
        dict["pid"] = message["pid"]
        dict["driver_id"] = message["driver_id"]
        dict["min_err"] = message["min_err"]

        # Validate and create a Report instance
        final_dict = SaveRequest(**dict)

        # Insert report into the database
        document = final_dict.model_dump(by_alias=True, exclude=["id"])
        result = self.db.matches.insert_one(document)

        if not result:
            logger.warning("was not able to create match result")
