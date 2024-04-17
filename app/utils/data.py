import json

# Extract data from GeoJSON features
def geojson_to_matrix(geojson_data):
    data = []
    for feature in geojson_data["features"]:
        latitude = feature["geometry"]["coordinates"][1]
        longitude = feature["geometry"]["coordinates"][0]
        time = feature["properties"]["time"]
        data.append([latitude, longitude, time])

    return data


# create geojson output
def feature_builder(lat, lng, t):
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lng, lat]},
        "properties": {"time": t},
    }


# Convert data to GeoJSON format
def matrix_to_geojson(matrix_data):
    geojson_features = []
    for point in matrix_data:
        lat, lng, time = point
        feature = feature_builder(lat, lng, time)
        geojson_features.append(feature)

    geojson = {"type": "FeatureCollection", "features": geojson_features}

    # Convert to JSON string
    return json.dumps(geojson, indent=4)
