from pymongo import MongoClient
from dotenv import load_dotenv
import certifi
import os

load_dotenv()  # load environment variables from .env file

# access environment variables
db_protocol = os.getenv("DB_PROTOCOL")
db_user = os.getenv("DB_USERNAME")
db_pass = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_params = os.getenv("DB_QUERY_PARAMS")
db_uri = os.getenv("DB_STRING")

print(db_uri)


# Database connection
# db_org = f"{db_protocol}://{db_user}:{db_pass}@{db_host}"

client = MongoClient("mongodb+srv://admin:iN9CUgIpDOflrebL@sharegocluster.qd9gubk.mongodb.net", tlsCAFile=certifi.where())
database = client.get_database("db")