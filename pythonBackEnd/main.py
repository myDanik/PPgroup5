from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import *
import psycopg2
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from schemas import User_Data
from SQL import Base, User, Route, Coordinate, Estimation, engine
import uuid
import random
import string



app = FastAPI(title='Veloapp')


Session = sessionmaker(engine)

@app.get("/users/{user_id}")
def get_user(user_id: int, route_id: int=None):
    session = Session()
    user = session.query(User).filter(User.UserID == user_id).first()
    routes = session.query(Coordinate).filter(Route.UserID == user_id and Coordinate.UserID == user_id).all()
    route_by_id = session.query(Coordinate).filter(Route.UserID == user_id and Coordinate.RouteID == route_id).first()
    session.close()
    if route_id == None:
        return user, routes
    else:
        return user, route_by_id

@app.post("/sign_up")
def post_sign_up(List: User_Data):
    session = Session()
    name = List.name
    login = List.login
    password = List.password
    token = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    user_id = str(uuid.uuid4().int)[:8]
    while session.query(User).filter(User.UserID == user_id).first():
        user_id = str(uuid.uuid4().int)[:8]
    while session.query(User).filter(User.Token == token).first():
        token = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    new_user = User(UserID=user_id, Name=name, Login=login, Password=password, Token=token)
    session.add(new_user)
    session.commit()

