from fastapi import FastAPI, HTTPException, Depends
from auth.database import User
from auth.jwt import generate_token
from auth.models import UserDB
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from auth.database import Base, User, Route, Coordinate, Estimation, engine
from auth.schemas import Route_Data
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session = sessionmaker(engine)

app = FastAPI(title='Veloapp')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users/")
def create_user(user_data: UserDB, db: Session = Depends(get_db)):
    token = generate_token()
    new_user = User(
        name=user_data.name,
        login=user_data.login,
        password=user_data.password,
        token=token
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message: "f"Success, {new_user.name}, welcome!", new_user}


@app.get("/users/{user_id}")
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"name": user.name, "id": user.id, "login": user.login, "token": user.token}


@app.put("/users/{user_id}")
def update_user(user_id: int, user_data: UserDB, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for attr, value in user_data.dict(exclude_unset=True).items():
        setattr(user, attr, value)
    db.commit()
    db.refresh(user)
    return {"message: "f"Success, user {user.name} was updated"}


@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.refresh(user)
    db.commit()
    return {"message: "f"Success, {user.name} with user id {user_id} was deleted"}

@app.get("/users_info/{user_id}")
def get_user(user_id: int, route_id: int=None):
    session = Session()
    user = session.query(User).filter(User.id == user_id).first()
    routes = session.query(Coordinate).filter(Route.user_id == user_id and Coordinate.user_id == user_id).all()
    route_by_id = session.query(Coordinate).filter(Route.user_id == user_id and Coordinate.route_id == route_id).first()
    session.close()
    if route_id == None:
        return user, routes
    else:
        return user, route_by_id

@app.get("/route_info/{route_id}")
def get_route(route_id: int):
    session = Session()
    route = session.query(Route).filter(Route.route_id == route_id).first()
    coordinates = session.query(Coordinate.latitude, Coordinate.longitude).filter(Coordinate.route_id==route_id).all()
    session.close()
    return route, coordinates
@app.post("/route/")
def post_route(route_info: Route_Data):
    session = Session()
    us_id = 1#session.query(User.id).filter(User.token==route_info.token).first()
    dist = None
    new_route = Route(route_id=route_info.route_id, user_id=us_id, estimation=None, distance=dist)
    session.add(new_route)
    for cord in range(len(route_info.latitude_longitude_cordid)):
        new_coordinates = Coordinate(route_id=route_info.route_id, user_id=us_id, latitude=route_info.latitude_longitude_cordid[cord][0],
                                     longitude=route_info.latitude_longitude_cordid[cord][1],
                                     cord_id=route_info.latitude_longitude_cordid[cord][2], operation_id=(max(session.query(Coordinate.operation_id).all()) + 1))
        session.add(new_coordinates)
@app.get("/free_route_id/")
def get_free_route_id():
    session = Session()
    return (max(session.query(Route.route_id).all()) + 1)