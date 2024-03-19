from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import *
import psycopg2
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'Users'
    UserID = Column(Integer, primary_key=True)
    Name = Column(String)
    Login = Column(String)
    Password = Column(String)
    Token = Column(String)
    routes = relationship("Route", back_populates="user")

class Route(Base):
    __tablename__ = 'Routes'
    RouteID = Column(Integer, primary_key=True)
    UserID = Column(Integer, ForeignKey('Users.UserID'))
    Latitude = Column(Float)
    Longitude = Column(Float)
    user = relationship("User", back_populates="routes")

app = FastAPI(title='Veloapp')

engine = create_engine('postgresql://postgres:123qweasdfghj@localhost:5432/app', echo=True)
Session = sessionmaker(engine)

@app.get("/users/{user_id}")
def get_user(user_id: int):
    session = Session()
    user = session.query(User).filter(User.UserID == user_id).first()
    session.close()
    return user