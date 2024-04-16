from dotenv import load_dotenv
from loguru import logger
import asyncio

# from datetime import datetime
load_dotenv()  # take environment variables from .env.

# database
from database.redis import client as redis_client
from database.mongodb import client as mongodb_client

# services
# from services.reddit import Reddit
# from services.clin import CLIN
# from services.pubsub import Publisher
# from services.compute import Compute

# logger configuration
logger.add("logs/{time}.log", rotation="12:00", compression="zip", enqueue=True)


# Redis Pub/Sub Message Listener
@logger.catch
async def listener(channel):
    async for message in channel.listen():
        if message["type"] == "message":
            logger.debug(message["data"].decode("UTF-8"))


async def main():
    # Info dump
    logger.success("server started")

    # Subscribe to main channel
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("main")

    # Start listener
    await asyncio.gather(listener(pubsub))


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.close()
