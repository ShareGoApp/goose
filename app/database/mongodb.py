from pymongo import MongoClient
from loguru import logger
import certifi


# utils
from utils.env import get_variable, environment

# get from environment
db_str = get_variable("DB_STRING")
client = MongoClient(db_str, tlsCAFile=certifi.where(), uuidRepresentation='standard', tz_aware=True)

# switch on environment
match environment:
    case 'dev': database = client.get_database("dev")
    case 'prod': database = client.get_database("db")
    case _: logger.error("unknown database requested")
