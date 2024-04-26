from loguru import logger
import redis.asyncio as redis
import os

# utils
from utils.env import get_variable, environment


def connect_local():
    logger.warning("[redis]: connecting to development database")

    # get from environment
    redis_host = os.getenv("REDIS_HOST")
    redis_port = int(os.getenv("REDIS_PORT"))
    redis_db = int(os.getenv("REDIS_DB"))
    redis_proto = int(os.getenv("REDIS_PROTOCOL"))

    # establish connection
    return redis.Redis(host=redis_host, port=redis_port, db=redis_db, protocol=redis_proto)

def connect_cloud():
    logger.info("[redis]: connecting to production database")

    # get from environment
    host = get_variable("REDIS_HOST")
    port = get_variable("REDIS_PORT")
    username = get_variable("REDIS_USER")
    password = get_variable("REDIS_PASS")

    # establish connection
    return redis.Redis(host=host, port=port, username=username, password=password)


match environment:
    case 'dev': client = connect_local()
    case 'prod': client = connect_cloud()
    case _: logger.error("[redis] failed to recognise env")
