from typing import Optional
from pydantic import BaseModel, Field


class RouteDB(BaseModel):
    id: Optional[int] = None
    latitude: float
    longitude: float
    user_id: int


class UserLogin(BaseModel):
    login: str = Field(max_length=64, nullable=True)
    password: str = Field(max_length=64, nullable=True)


class UserDB(UserLogin):
    name: str = Field(min_length=3, max_length=64)


class Coordinate_get(BaseModel):
    latitude: float = Field(nullable=False, ge=-90.0, le=90.0)
    longitude: float = Field(nullable=False, ge=-180.0, le=180.0)


class Estimation_get(BaseModel):
    route_id: int
    estimation: float = Field(le=5, ge=1)
