# path: utils/time.py
from datetime import datetime
import numpy as np
import json


# convert datetime strings to unix format
def convert_to_unix(timestamp) -> float:
    datetime_obj = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    unix_time = datetime_obj.timestamp()
    return unix_time


# convert geojson point features to numpy.ndarray
def geojson_to_ndarray(geojson_data, logger):
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
def destructure_message(message, logger):
    try:
        # Deserialize message, ex: geo_request:{json}
        data = message["data"].decode("utf-8")
        type_info, payload = data.split(":", 1)
        payload = json.loads(payload)
    except:
        logger.warning("failed to destructure message")
        return

    return type_info, payload


# DEPRICATED: extract data from GeoJSON features
def geojson_to_matrix(geojson_data):
    data = []
    for feature in geojson_data["features"]:
        latitude = feature["geometry"]["coordinates"][1]
        longitude = feature["geometry"]["coordinates"][0]
        time = feature["properties"]["time"]
        data.append([latitude, longitude, time])
    return data


# DEPRICATED: convert json string data to numpy matrices
def matrix_to_ndarray(self, matrix):
    try:
        # Convert the timestamps to Unix time using pandas (you could also use datetime module in Python)
        timestamps = [self.convert_to_unix(date) for _, _, date in matrix]
        # Create a numpy array for latitudes, longitudes, and Unix timestamps
        latitudes = np.array([lat for lat, _, _ in matrix])
        longitudes = np.array([lng for _, lng, _ in matrix])
        timestamps = np.array(timestamps)
        self.logger.success("succesfully converted data")
        return np.array(list(zip(latitudes, longitudes, timestamps)))
    except:
        self.logger.error("failed to convert data to np matrix")
        return None
