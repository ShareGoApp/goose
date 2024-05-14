import uuid
from datetime import datetime, UTC
from pydantic import BaseModel, Field
import random

class Preferences(BaseModel):
    """ User preferences used while matching a ride """
    smoking_allowed: bool = True
    pets_allowed: bool = True
    small_talk: bool = True

def random_animal_picture():
    animals = {
        "koala" : "https://cdn-icons-png.flaticon.com/128/3069/3069172.png",
        "turtle" : "https://cdn-icons-png.flaticon.com/128/2977/2977402.png",
        "lion" : "https://cdn-icons-png.flaticon.com/128/616/616412.png",
        "fox" : "https://cdn-icons-png.flaticon.com/128/2153/2153090.png",
        "bee" : "https://cdn-icons-png.flaticon.com/128/809/809052.png",
        "cow" : "https://cdn-icons-png.flaticon.com/128/1998/1998610.png",
        "chicken" : "https://cdn-icons-png.flaticon.com/128/2632/2632839.png"
    }

    chosen = random.choice(list(animals.keys()))
    return animals[chosen]

class User(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    auth0_id: str
    test_user: bool = Field(default=False)
    name: str
    email: str
    phone_number: str
    picture: str = Field(default_factory=random_animal_picture, description="user's profile picture id")   
    rating: float = Field(default=1.0, description="user's rating")                 
    preferences: Preferences = Field(default=Preferences())
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))