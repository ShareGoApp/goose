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

    # convert json string data to numpy matrices
    def convert_data(self, matrix):
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
