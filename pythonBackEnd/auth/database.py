# from pydantic import EmailStr
from pydantic import EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from PPgroup5.pythonBackEnd.pg import url

Base = declarative_base()
engine = create_engine(url)
Session = sessionmaker(engine)
session = Session()


def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String)
    telephone_number = Column(String)
    surname = Column(String)
    patronymic = Column(String)
    location = Column(String)
    # True = male, False = female
    sex = Column(Boolean)
    hashed_password = Column(String, nullable=False)
    salt_hashed_password = Column(String, nullable=False)
    token_mobile = Column(String, nullable=False)
    routes = relationship("Route", back_populates="user")


class Route(Base):
    __tablename__ = 'routes'
    route_id = Column(Integer, primary_key=True, unique=True, nullable=False, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    distance = Column(Float)
    user = relationship("User", back_populates="routes")
    estimations = relationship("Estimation", back_populates="route")
    coordinates = relationship("Coordinate", back_populates="routes")


class Coordinate(Base):
    __tablename__ = 'coordinates'
    route_id = Column(Integer, ForeignKey('routes.route_id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    cord_id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    operation_time = Column(DateTime, nullable=False)
    routes = relationship("Route", back_populates="coordinates")


class Estimation(Base):
    __tablename__ = 'estimations'
    estimation_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    route_id = Column(Integer, ForeignKey('routes.route_id'), nullable=False)
    estimation_value = Column(Float, nullable=False)
    user_id = Column(Integer, nullable=False)
    estimator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    datetime = Column(DateTime, nullable=False)
    route = relationship("Route", back_populates="estimations")


Base.metadata.create_all(engine)
