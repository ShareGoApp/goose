from dotenv import load_dotenv
from loguru import logger
import redis.asyncio as redis
import os

# utils
from utils.env import get_variable, environment


# access environment variables
if environment == "dev":
    # get from environment
    redis_host = os.getenv("REDIS_HOST")
    redis_port = int(os.getenv("REDIS_PORT"))
    redis_db = int(os.getenv("REDIS_DB"))
    redis_proto = int(os.getenv("REDIS_PROTOCOL"))

    # establish connection
    client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, protocol=redis_proto)

if environment == "prod":
    # get from environment
    host = get_variable("REDIS_HOST")
    port = get_variable("REDIS_PORT")
    username = get_variable("REDIS_USER")
    password = get_variable("REDIS_PASS")

    # establish connection
    client = redis.Redis(host=host, port=port, username=username, password=password)
