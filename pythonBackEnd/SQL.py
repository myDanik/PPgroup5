from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'Users'
    UserID = Column(Integer, primary_key=True)
    Name = Column(String, nullable=False)
    Login = Column(String, nullable=False)
    Password = Column(String, nullable=False)
    Token = Column(String, nullable=False)
    routes = relationship("Route", back_populates="user")

class Route(Base):
    __tablename__ = 'Routes'
    RouteID = Column(Integer, primary_key=True, unique=True, nullable=False)
    UserID = Column(Integer, ForeignKey('Users.UserID'), nullable=False)
    Estimation = Column(Float)
    Distance = Column(Float)
    user = relationship("User", back_populates="routes")
    coordinates = relationship("Coordinate", back_populates="route")
    estimations = relationship("Estimation", back_populates="route")

class Coordinate(Base):
    __tablename__ = 'Coordinates'
    RouteID = Column(Integer, ForeignKey('Routes.RouteID'), nullable=False)
    UserID = Column(Integer, ForeignKey('Users.UserID'), nullable=False)
    Latitude = Column(Float, nullable=False)
    Longitude = Column(Float, nullable=False)
    Cord_id = Column(Integer, primary_key=True, nullable=False)
    route = relationship("Route", back_populates="coordinates")

class Estimation(Base):
    __tablename__ = 'Estimation'
    EstimID = Column(Integer, primary_key=True, nullable=False)
    RouteID = Column(Integer, ForeignKey('Routes.RouteID'), nullable=False)
    Estim = Column(Float, nullable=False)
    UserID = Column(Integer, ForeignKey('Users.UserID'), nullable=False)
    route = relationship("Route", back_populates="estimations")


engine = create_engine('postgresql://postgres:123qweasdfghj@localhost:5432/app')

Base.metadata.create_all(engine)
