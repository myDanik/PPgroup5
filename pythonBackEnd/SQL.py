from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
import psycopg2


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

engine = create_engine('postgresql://postgres:123qweasdfghj@localhost:5432/app')
Base.metadata.create_all(engine)