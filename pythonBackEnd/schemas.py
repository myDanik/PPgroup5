from pydantic import BaseModel


class User_Data(BaseModel):
    name: str
    login: str
    password: str
