from pydantic import BaseModel, validator
from typing import List

class Route_Data(BaseModel):
    route_id: int
    latitude_longitude_cordid: List[List[int]]
    token: str

    @validator('latitude_longitude_cordid', each_item=True)
    def check_list_length(cls, v):
        if len(v) != 3:
            raise ValueError('List must contain exactly 3 sublists')
        return v


