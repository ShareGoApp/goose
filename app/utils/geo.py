import math

# Calculate the distance between two points on the 
# Earth's surface using Haversine formula.
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of the Earth in kilometers
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) * math.sin(d_lat / 2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) * math.sin(
        d_lon / 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = R * c
    return d


# used to extend line segments for finer control.
def intermediate_points(lat1, lon1, lat2, lon2, n):
    intermediate_points = []
    total_distance = haversine(lat1, lon1, lat2, lon2)
    segment_distance = total_distance / (n + 1)  # n+2 points including the start and end points
    for i in range(1, n + 1):
        f = segment_distance * i / total_distance
        lat = lat1 + f * (lat2 - lat1)
        lon = lon1 + f * (lon2 - lon1)
        intermediate_points.append((lat, lon))
    return intermediate_points


# Find the closest pair of points between two sets of points.
def closest_pair(points1, points2):
    min_distance = float("inf")
    closest_point_pair = None
    for p1 in points1:
        for p2 in points2:
            d = haversine(p1[0], p1[1], p2[0], p2[1])
            if d < min_distance:
                min_distance = d
                closest_point_pair = (p1, p2)
    return closest_point_pair, min_distance
