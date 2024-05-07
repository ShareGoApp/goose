from database.redis import client as redis
import json

# publish geo-lookup requests in redis 
async def geo_publish(data):
    serialized_message = json.dumps(data)
    await redis.publish("main", f"geo_request:{serialized_message}")

# publish requests matching in redis 
async def mat_publish(data):
    serialized_message = json.dumps(data)
    await redis.publish("main", f"mat_request:{serialized_message}")

# publish match save request in redis 
async def sav_publish(data):
    serialized_message = json.dumps(data)
    await redis.publish("main", f"sav_request:{serialized_message}")