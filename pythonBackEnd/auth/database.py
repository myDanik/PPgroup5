from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
from pg import url
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    login = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    salt_hashed_password = Column(String, nullable=False)
    token_mobile = Column(String, nullable=False)
    routes = relationship("Route", back_populates="user")


# class Association_routes_cords(Base):
#     __tablename__ = 'route_coordinate_association',
#     route_id = Column(Integer, ForeignKey('routes.route_id'), primary_key=True)
#     cord_id = Column(Integer, ForeignKey('coordinates.cord_id'), primary_key=True)


class Route(Base):
    __tablename__ = 'routes'
    route_id = Column(Integer, primary_key=True, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    estimation = Column(Float)
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
    estim_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    route_id = Column(Integer, ForeignKey('routes.route_id'), nullable=False)
    estim = Column(Float, nullable=False)
    user_id = Column(Integer, nullable=False)
    estimator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    datetime = Column(DateTime, nullable=False)
    route = relationship("Route", back_populates="estimations")


engine = create_engine(url)

Base.metadata.create_all(engine)
