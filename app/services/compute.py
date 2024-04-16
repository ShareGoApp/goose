"""
    The Idea of this class is to contain all of the functionality
    required to perform dynamic time warping on passenger and drivers
"""

from tslearn.metrics import dtw
import numpy as np

# utils
from utils.time import convert_to_unix

class Compute:
    def __init__(self):
        pass

    def convert_data(matrix):
        # Convert the timestamps to Unix time using pandas (you could also use datetime module in Python)
        timestamps = [convert_to_unix(date) for _ , _ , date in matrix]

        # Create a numpy array for latitudes, longitudes, and Unix timestamps
        latitudes = np.array([lat for lat, _, _ in matrix])
        longitudes = np.array([lng for _, lng, _ in matrix])
        timestamps = np.array(timestamps)

        return np.array(list(zip(latitudes, longitudes, timestamps)))
    
    def compute_distance(passenger, drivers):
        return dtw()