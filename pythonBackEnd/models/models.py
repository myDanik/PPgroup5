from typing import Optional, Union

from pydantic import BaseModel, Field


class RouteDB(BaseModel):
    id: Optional[int] = None
    latitude: float
    longitude: float
    user_id: int


class UserDB(BaseModel):
    login: str = Field(nullable=False)
    password: str = Field(min_length=3, max_length=64, nullable=False)
    name: str = Field(min_length=3, max_length=64, nullable=False)
    email: Union[str, None] = None
    telephone_number: Union[str, None] = None
    surname: Union[str, None] = None
    patronymic: Union[str, None] = None
    location: Union[str, None] = None
    sex: Union[bool, None] = None


class Coordinate_get(BaseModel):
    latitude: float = Field(nullable=False, ge=-90.0, le=90.0)
    longitude: float = Field(nullable=False, ge=-180.0, le=180.0)


class Estimation_get(BaseModel):
    route_id: int
    estimation: float = Field(le=5, ge=1)
