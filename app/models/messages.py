from pydantic import BaseModel
from typing import List
from enum import Enum


class MsgTypes(Enum):
    valid: 0
    invalid: 1

# message for match request
class MatchRequest(BaseModel):
    type: str
    passenger_id: str
    driver_ids: List[str]

# message for geo request
class GeoRequest(BaseModel):
    type: str
    passenger_id: str
    max_radius: int
    
