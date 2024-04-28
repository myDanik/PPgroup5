from typing import Optional
from pydantic import BaseModel, Field


class RouteDB(BaseModel):
    id: Optional[int] = None
    latitude: float
    longitude: float
    user_id: int


class UserDB(BaseModel):
    name: str = Field(min_length=3, max_length=64)
    login: str = Field(min_length=6, max_length=64)
    password: str = Field(min_length=4, max_length=64)


class User_login(BaseModel):
    login: str = Field(max_length=64, nullable=True)
    password: str = Field(max_length=64, nullable=True)


class Coordinate_get(BaseModel):
    latitude: float = Field(nullable=False, ge=-90.0, le=90.0)
    longitude: float = Field(nullable=False, ge=-180.0, le=180.0)


class Estimation_get(BaseModel):
    route_id: int
    estim: float = Field(le=10, ge=1)

