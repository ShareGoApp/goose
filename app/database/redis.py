import redis.asyncio as redis
from dotenv import load_dotenv
import os

load_dotenv()  # load environment variables from .env file

# access environment variables
redis_host  = os.getenv("REDIS_HOST")
redis_port  = int(os.getenv("REDIS_PORT"))
redis_db    = int(os.getenv("REDIS_DB"))
redis_proto = int(os.getenv("REDIS_PROTOCOL"))

# Redis connection
client = redis.Redis(
    host=redis_host, port=redis_port, db=redis_db, protocol=redis_proto
)