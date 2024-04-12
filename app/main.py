import asyncio
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()  # take environment variables from .env.

# Database
# from database.redis import client as redis_client

# Utils
# from utils.protobuf import deserialize_analytics_request
# from utils.protobuf import deserialize_report_request
# from utils.report import create_report

# Services
# from services.reddit import Reddit
# from services.clin import CLIN
# from services.pubsub import Publisher

async def await_5():
    pass

async def await_1():
    pass


async def main():
    # Create a Redis client
    # client = redis.Redis(host="host.docker.internal", port=6379, db=0, protocol=3)

    # Subscribe to main channel
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("main")

    # Start listener
    await asyncio.gather(listener(pubsub))

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()