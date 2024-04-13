from typing import Optional
from pydantic import BaseModel, Field


class RouteDB(BaseModel):
    id: Optional[int] = None
    latitude: float
    longitude: float
    user_id: int

class UserDB(BaseModel):
    name: str = Field(min_length=3, max_length=128)
    login: str = Field(min_length=6, max_length=1024)
    password: str = Field(min_length=6, max_length=1024)
    token: str


