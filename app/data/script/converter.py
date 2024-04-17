import json

data = [
    [40.747876, -73.988074, "2024-04-09T11:00:00Z"],
    [40.748876, -73.987074, "2024-04-09T11:05:00Z"],
    [40.749876, -73.986074, "2024-04-09T11:10:00Z"],
    [40.750876, -73.985074, "2024-04-09T11:15:00Z"],
]


# Convert data to GeoJSON format
geojson_features = []
for point in data:
    latitude, longitude, time = point
    feature = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [longitude, latitude]},
        "properties": {"time": time},
    }
    geojson_features.append(feature)

geojson = {"type": "FeatureCollection", "features": geojson_features}

# Convert to JSON string
geojson_str = json.dumps(geojson, indent=4)

# Write the GeoJSON string to a file
with open("converted.json", "w") as file:
    file.write(geojson_str)

print("GeoJSON data has been written to converted.json.")
