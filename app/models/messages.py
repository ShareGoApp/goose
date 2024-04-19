from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

# message for match request
class MatchRequest(BaseModel):
    passenger_id: str
    driver_ids: List[str]

# message for geo request
class GeoRequest(BaseModel):
    passenger_id: str
    max_radius: int

# message for save request
class SaveRequest(BaseModel):
    created_at: datetime = Field(..., description="Timestamp of report submission") # Metadata
    passenger_id: str
    driver_id: str
    min_err: float