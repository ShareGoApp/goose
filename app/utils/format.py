# path: utils/time.py
from datetime import datetime
import numpy as np

# convert datetime strings to unix format
def convert_to_unix(timestamp) -> float:
    datetime_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    unix_time = datetime_obj.timestamp()
    return unix_time

# convert geojson point features to numpy.ndarray
def geojson_to_ndarray(logger, geojson_data):
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