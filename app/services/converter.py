"""
    The Idea of this class is to contain all of the functionality
    required to perform dynamic time warping on passenger and drivers
"""

from datetime import datetime
import numpy as np


class Converter:
    def __init__(self, logger):
        self.logger = logger

    # convert timestamp strings to unix time
    def convert_to_unix(self, timestamp) -> float:
        try:
            self.logger.debug("converting to unix")
            datetime_obj = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            unix_time = datetime_obj.timestamp()
            return unix_time
        except:
            return self.logger.error("failed to convert unix")
        

    # Extract data from GeoJSON features
    def geojson_to_matrix(geojson_data):
        data = []
        for feature in geojson_data["features"]:
            latitude = feature["geometry"]["coordinates"][1]
            longitude = feature["geometry"]["coordinates"][0]
            time = feature["properties"]["time"]
            data.append([latitude, longitude, time])

        return data


    # convert json string data to numpy matrices
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
        

    def geojson_to_ndarray(self, geojson_data):
        try:
            data = []
            for feature in geojson_data["features"]:
                latitude = feature["geometry"]["coordinates"][1]
                longitude = feature["geometry"]["coordinates"][0]
                time = feature["properties"]["time"]
                unix_time = self.convert_to_unix(time)
                data.append([latitude, longitude, unix_time])
            
            if not data:
                return None
            
            return np.array(data)
        except Exception as e:
            self.logger.error(f"An error occurred: {str(e)}")
            return None

