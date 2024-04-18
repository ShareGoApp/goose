from pydantic import BaseModel
from typing import List

# message for match request
class MatchRequest(BaseModel):
    passenger_id: str
    driver_ids: List[str]

# message for geo request
class GeoRequest(BaseModel):
    passenger_id: str
    max_radius: int

# message for save request
class CreateRequest(BaseModel):
    passenger_id: str
    driver_id: str