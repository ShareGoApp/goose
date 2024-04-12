import asyncio
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()  # take environment variables from .env.

# database
from database.redis import client as redis_client
# from database.mongodb import client as mongodb_client

# services
# from services.reddit import Reddit
# from services.clin import CLIN
# from services.pubsub import Publisher
from services.compute import Compute

async def await_5():
    pass

async def await_1():
    pass

# Redis Pub/Sub Message Listener
async def listener(channel):
    async for message in channel.listen():
        if message["type"] == "message":
            # Destructure message
            type_identifier, data = destruct_message(message)

            match type_identifier:
                case "AnalyticsRequest":
                    print("Service: received START message")
                    await handle_analytics_request(data)

                case "ReportRequest":
                    print("Service: received notification")
                    await handle_report_request(data)

                case _:
                    print("Service: received unknown message")
                    pass



async def main():
    # Subscribe to main channel
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("main")

    # Start listener
    await asyncio.gather(listener(pubsub))

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()