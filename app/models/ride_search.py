from pydantic_extra_types.coordinate import Coordinate
from pydantic import BaseModel, Field
from datetime import datetime, UTC
from enum import Enum
import uuid

# models
from models.ride import Address, Route

class RideSearch(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    passenger: uuid.UUID
    start_address: Address
    destination_address: Address
    departure: datetime
    max_deviation: int = Field(..., description="Max diversion from original tour")
    route: Route
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))