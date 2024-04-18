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
db_uri = os.getenv("DB_URI")


# Database connection
db_org = f"{db_protocol}://{db_user}:{db_pass}@{db_host}"

# FIXME: something is weird here
print("org: " + db_org)
print("new: " + db_uri)
print(db_uri == db_org)


client = MongoClient(db_uri, tlsCAFile=certifi.where())
database = client.get_database("db")