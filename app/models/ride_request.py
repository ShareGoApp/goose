from pydantic import BaseModel, Field
from datetime import datetime, UTC
from enum import Enum
import uuid

# models
from models.ride import Route, Stop

class RideRequestStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"
    cancelled = "cancelled" 

class RideRequest(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    requester: uuid.UUID        # User
    driver: uuid.UUID           # User
    ride: uuid.UUID             # Ride
    match: uuid.UUID            # RideMatch. Match that this request originated from
    original_search: uuid.UUID  # Ride Search
    planned_stops: list[Stop]   # The stops of how accepting this request will look like
    planned_route: Route        # The route of how accepting this request will look like
    status: RideRequestStatus
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))