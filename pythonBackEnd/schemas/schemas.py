from pydantic import BaseModel, validator, EmailStr
from typing import List
from fastapi import HTTPException


class Route_Data(BaseModel):
    route_id: int
    latitude_longitude_cordid: List[List[int]]
    token: str

    @validator('latitude_longitude_cordid', each_item=True)
    def check_list_length(cls, v):
        if len(v) != 3:
            raise ValueError('List must contain exactly 3 sublists')
        return v


def has_not_permission_error(permission):
    if not permission:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "data": None,
            "details": "No permission"
        })


def not_found_error(arg, name):
    if not arg:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "data": None,
            "details": f"{name} not found"
        })
