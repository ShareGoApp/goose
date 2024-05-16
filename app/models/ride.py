from pydantic_extra_types.coordinate import Coordinate
from pydantic import BaseModel, Field
from datetime import datetime, UTC
from enum import Enum
import uuid


class LineString(BaseModel):
    type: str
    coordinates: list[list[float]]

class Route(BaseModel):
    distance: float
    expected_travel_time: float
    shape: LineString
    timestamps: list[datetime]

class Address(BaseModel):
    street: str
    country: str
    city: str
    province: str
    postal_code: str
    coordinate: Coordinate

class Passenger(BaseModel):
    profile: uuid.UUID # User
    start: Address
    destination: Address

class StopType(str, Enum):
    pickup = "pickup"
    dropoff = "dropoff"

class Stop(BaseModel):
    passenger_index: int # The passenger that this stop is for
    type: StopType
    duration: float # Duration to get to this stop from the previous stop
    distance: float # Distance to this stop from the previous stop

class RideStatus(str, Enum):
    open = "open"
    full = "full"
    finished = "finished"
    cancelled = "cancelled"

class Ride(BaseModel):
    id: uuid.UUID = Field(alias="_id")
    driver: uuid.UUID # User
    seats_total: int = Field(..., description="Free seats, drivers seat is not counted")
    seats_available: int
    start_address: Address
    destination_address: Address
    passengers: list[Passenger] = Field(..., description="list of passengers for the ride")
    departure: datetime = Field(..., description="timestamp of ride departure")
    max_deviation: int = Field(..., description="max deviation from orignal route in meters")
    status: RideStatus  = Field(..., description="ride availability status")
    stops: list[Stop] = Field(default=[], description="the stops that this route goes through. This is not including the drivers' start and destination. The individual stop in stops are in-order of route traversal. So stop[0] will be the first stop of the ride stop[1] the secondth' and so on") #
    route: Route
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))