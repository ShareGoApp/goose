from datetime import datetime, UTC
from enum import Enum
import uuid
from pydantic import BaseModel, Field

from app.models.ride import Ride
from app.models.ride_search import RideSearch

class RideMatch(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    passenger_id: uuid.UUID # User
    search_id: uuid.UUID # RideSearch
    ride_id: uuid.UUID # Ride
    seen: bool # Wheter or not this match has been seen by the passenger
    similarity: float # How close the search was to the ride @Note - This was renamed from min_err
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))