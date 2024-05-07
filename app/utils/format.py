# path: utils/time.py
from datetime import datetime
from tslearn.metrics import dtw
from loguru import logger
import numpy as np
import json


# convert datetime strings to unix format
def convert_to_unix(timestamp) -> float:
    datetime_obj = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    unix_time = datetime_obj.timestamp()
    return unix_time


# convert geojson point features to numpy.ndarray
def geojson_to_ndarray(geojson_data):
    try:
        data = []
        for feature in geojson_data["features"]:
            latitude = feature["geometry"]["coordinates"][1]
            longitude = feature["geometry"]["coordinates"][0]
            time = feature["properties"]["time"]
            unix_time = convert_to_unix(time)
            data.append([latitude, longitude, unix_time])

        if not data:
            return None

        return np.array(data)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return None


# destructuring incoming messages
def destructure_message(message):
    try:
        # Deserialize message, ex: geo_request:{json}
        data = message["data"].decode("utf-8")
        type_info, payload = data.split(":", 1)
        payload = json.loads(payload)
        return type_info, payload
    except:
        return


def map_distance(passenger, driver):
    driver_matrix = geojson_to_ndarray(driver)
    return {id: driver["_id"], "dist": dtw(passenger, driver_matrix)}
