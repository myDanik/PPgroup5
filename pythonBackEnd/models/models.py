from typing import Optional, Union, List
from pydantic import BaseModel, Field


class RouteDB(BaseModel):
    id: Optional[int] = None
    latitude: float
    longitude: float
    user_id: int


class MyUserIn(BaseModel):
    password: str = Field(min_length=3, max_length=64)
    name: str = Field(min_length=3, max_length=64)
    email: Union[str, None] = None
    telephone_number: Union[str, None] = None
    surname: Union[str, None] = None
    patronymic: Union[str, None] = None
    location: Union[str, None] = None
    sex: Union[bool, None] = None


class MyUserOut(BaseModel):
    id: int
    name: str
    email: Union[str, None] = None
    telephone_number: Union[str, None] = None
    surname: Union[str, None] = None
    patronymic: Union[str, None] = None
    location: Union[str, None] = None
    sex: Union[bool, None] = None
    token_mobile: str


class OtherUserOut(BaseModel):
    id: int
    name: str
    surname: Union[str, None] = None
    patronymic: Union[str, None] = None
    location: Union[str, None] = None
    sex: Union[bool, None] = None


class RouteGet(BaseModel):
    users_travel_time: int
    comment: str


class CoordinateGet(BaseModel):
    latitude: float = Field(nullable=False, ge=-90.0, le=90.0)
    longitude: float = Field(nullable=False, ge=-180.0, le=180.0)


class CoordinatesInfoOut(BaseModel):
    cord_id: int
    route_id: int
    user_id: int
    latitude: float
    longitude: float
    order: int
    locname: str


class EstimationGet(BaseModel):
    route_id: int
    estimation: float = Field(le=5, ge=1)
    comment: str
