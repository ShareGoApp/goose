import json


class RedisService():
    def __init__(self, client):
        self.client = client

    async def push_request(self, type_info, data):
        serialized_message = json.dumps(data)
        await self.client.publish("main", f"{type_info}:{serialized_message}")

    # Handle publishing request for Analytics
    async def push_geo_request(self, data):
        type_info = "geo_request"
        serialized_message = json.dumps(data)
        await self.client.publish("main", f"{type_info}:{serialized_message}")

    # Handle publishing request for Post Reports
    async def push_match_request(self, data):
        type_info = "mat_request"
        serialized_message = json.dumps(data)
        await self.client.publish("main", f"{type_info}:{serialized_message}")

    async def push_save_reqest(self, data):
        type_info = "sav_request"
        serialized_message = json.dumps(data)
        await self.client.publish("main", f"{type_info}:{serialized_message}")
    

    