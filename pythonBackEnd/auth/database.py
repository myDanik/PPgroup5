from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, MetaData
from sqlalchemy.orm import declarative_base, relationship
import psycopg2

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    login = Column(String, nullable=False)
    password = Column(String, nullable=False)
    token = Column(String, nullable=False)
    routes = relationship("Route", back_populates="user")


class Route(Base):
    __tablename__ = 'routes'
    route_id = Column(Integer, primary_key=True, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    estimation = Column(Float)
    distance = Column(Float)
    user = relationship("User", back_populates="routes")
    coordinates = relationship("Coordinate", back_populates="route")
    estimations = relationship("Estimation", back_populates="route")


class Coordinate(Base):
    __tablename__ = 'coordinates'
    route_id = Column(Integer, ForeignKey('routes.route_id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    cord_id = Column(Integer, primary_key=True, nullable=False)
    route = relationship("Route", back_populates="coordinates")


class Estimation(Base):
    __tablename__ = 'estimations'
    estim_id = Column(Integer, primary_key=True, nullable=False)
    route_id = Column(Integer, ForeignKey('routes.route_id'), nullable=False)
    estim = Column(Float, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    route = relationship("Route", back_populates="estimations")


engine = create_engine('postgresql://postgres:postgres@localhost:5432/postgres')
Base.metadata.create_all(engine)
