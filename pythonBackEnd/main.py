import datetime
from geopy.distance import great_circle as GC
from geopy.geocoders import Nominatim
from datetime import timedelta
from fastapi import FastAPI, HTTPException, Depends
from PPgroup5.pythonBackEnd.auth.tokens_hashs import (creating_hash_salt, authenticate_user, create_token, token_user,
                                                      generate_token)
from PPgroup5.pythonBackEnd.auth.models import UserDB, User_login, Coordinate_get, Estimation_get
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker
from PPgroup5.pythonBackEnd.auth.database import User, Route, Coordinate, engine, Estimation
from PPgroup5.pythonBackEnd.auth.schemas import Route_Data


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session = sessionmaker(engine)
#
app = FastAPI(title='Veloapp')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/authorization")
def create_user(user_data: UserDB, db: Session = Depends(get_db)):
    if db.query(User).filter(User.login == user_data.login).first():
        raise HTTPException(status_code=409, detail="Login is already exists")
    token_mobile = generate_token()
    generated_salt, hashed_password = creating_hash_salt(user_data.password)
    new_user = User(
        name=user_data.name,
        login=user_data.login,
        hashed_password=hashed_password,
        token_mobile=token_mobile,
        salt_hashed_password=generated_salt
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    token = create_token(new_user.id, timedelta(hours=12))
    return {"token": token, "message": f"Success, {new_user.name}, welcome!"}


@app.post("/login")
def login(login_user: User_login, entry_token: str = None, db: Session = Depends(get_db)):
    if token_user(entry_token):
        user_id = token_user(entry_token)
        if user_id:
            db_user = db.query(User).filter(User.id == user_id).first()
            if db_user:
                return {"token": entry_token, "message": f"Hello, {db_user.name}"}
            else:
                raise HTTPException(status_code=401, detail="Invalid token")
    db_user = db.query(User).filter(User.login == login_user.login).first()
    if db_user:
        if authenticate_user(login_user.password, db_user.hashed_password, db_user.salt_hashed_password):
            token = create_token(db_user.id, timedelta(hours=2))
            return {"token": token, "message": f"Hello, {db_user.name}"}
    raise HTTPException(status_code=401, detail="Incorrect login or password")


@app.get("/users/{user_id}")
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"name": user.name, "id": user.id, "login": user.login, "token_mobile": user.token_mobile}


@app.put("/users/{user_id}", )
def update_user(user_id: int, user_data: UserDB, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    generated_salt, hashed_password = creating_hash_salt(user_data.password)
    user_data = user_data.dict()
    del user_data["password"]
    user_data["hashed_password"] = hashed_password
    user_data["salt_hashed_password"] = generated_salt
    for attr, value in user_data.items():
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
    # delete his routes
    return {"message": f"Success, {user.name} with user id {user_id} was deleted"}


@app.get("/users_info/{user_id}")
def get_user(user_id: int, route_id: int = None):
    session = Session()
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    routes = session.query(Coordinate).filter((Coordinate.user_id == user_id)).all()
    route_by_id = session.query(Coordinate).filter((Coordinate.user_id == user_id),(Coordinate.route_id == route_id)).all()
    session.close()
    if route_id is None:
        return {"routes": routes, "name": user.name, "id": user.id, "login": user.login, "token_mobile": user.token_mobile}
    else:
        return {"routes": route_by_id, "name": user.name, "id": user.id, "login": user.login, "token_mobile": user.token_mobile}


# не работает
@app.get("/route_info/{route_id}")
def get_route(route_id: int):
    session = Session()
    route = session.query(Route).filter(Route.route_id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    coordinates = session.query(Coordinate).filter(Coordinate.route_id == route_id).all()
    geoLoc = Nominatim(user_agent="GetLoc")
    locname = geoLoc.reverse(str(session.query(Coordinate.latitude).filter(Coordinate.route_id == route_id).first())[1:-2] + ", " + str(session.query(Coordinate.longitude).filter(Coordinate.route_id == route_id).first())[1:-2])
    session.close()
    return route, coordinates, str(locname)


@app.post("/route/")
def post_route(route_info: Route_Data):
    session = Session()
    user_id = session.query(User.id).filter(User.token==route_info.token).first()
    dist = 0
    for i in range(len(route_info.latitude_longitude_cordid)-1):
        dist += GC((route_info.latitude_longitude_cordid[i][0], route_info.latitude_longitude_cordid[i][1]), (route_info.latitude_longitude_cordid[i+1][0], route_info.latitude_longitude_cordid[i+1][1])).km
    new_route = Route(route_id=route_info.route_id, user_id=user_id, estimation=None, distance=dist)
    session.add(new_route)
    for cord in range(len(route_info.latitude_longitude_cordid)):
        new_coordinates = Coordinate(route_id=route_info.route_id, user_id=user_id,
                                     latitude=route_info.latitude_longitude_cordid[cord][0],
                                     longitude=route_info.latitude_longitude_cordid[cord][1],
                                     cord_id=route_info.latitude_longitude_cordid[cord][2],
                                     operation_time=datetime.datetime.now())
        session.add(new_coordinates)


@app.get("/free_route_id/")
def get_free_route_id():
    session = Session()
    max_route_id = session.query(func.max(Route.route_id)).scalar()
    return {"free_route_id": max_route_id+1}


@app.get("/token_mobile/{token_mobile}")
def check_token(token_mobile: str):
    session = Session()
    user = session.query(User).filter(User.token_mobile == token_mobile).first()
    if not user:
        raise HTTPException(status_code=404, detail="Token not found")
    else:
        return {"name": user.name, "id": user.id, "login": user.login, "token_mobile": user.token_mobile}


# coordinates
@app.get("/coordinates/{user_id}/")
def get_coordinates_by_id(user_id: int, db: Session = Depends(get_db)):
    coordinates = db.query(Coordinate).filter(Coordinate.user_id == user_id).all()
    return coordinates


@app.post("/coordinates/{user_id}")
def create_coordinate_point(user_id: int, coordinate_data: Coordinate_get, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_coordinate = Coordinate(
        user_id=user_id,
        latitude=coordinate_data.latitude,
        longitude=coordinate_data.longitude,
        operation_time=datetime.datetime.now()
    )
    db.add(new_coordinate)
    db.commit()
    db.refresh(new_coordinate)
    return new_coordinate


@app.put("/coordinates/{user_id}")
def update_coordinate_point(user_id: int, cord_id: int, coordinate_data: Coordinate_get, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    coordinate = db.query(Coordinate).filter(Coordinate.cord_id == cord_id).first()
    if not coordinate:
        raise HTTPException(status_code=404, detail="Coordinate not found")
    coordinate.latitude = coordinate_data.latitude
    coordinate.longitude = coordinate_data.longitude
    coordinate.operation_time = datetime.datetime.now()
    db.commit()
    db.refresh(user)
    return {
        "user_id": user_id,
        "latitude": coordinate_data.latitude,
        "longitude": coordinate_data.longitude,
        "cord_id": cord_id,
        "message": f"Success, coordinate was updated"
    }


@app.delete("/coordinate/{cord_id}")
def delete_coordinate_point(user_id: int, cord_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    coordinate = db.query(Coordinate).filter(Coordinate.cord_id == cord_id).first()
    if not coordinate:
        raise HTTPException(status_code=404, detail="Coordinate not found")
    db.delete(coordinate)
    db.refresh(coordinate)
    db.commit()
    return {"message": f"Success, {cord_id} was deleted"}


# estimations
@app.post("/routes/estimations/{route_id}")
def create_estimation(user_id: int, estimator_data: Estimation_get, db: Session = Depends(get_db)):
    route = db.query(Route).filter(Route.route_id == estimator_data.route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    user = db.query(Estimation).filter(Estimation.user_id == user_id).first()
    if user:
        raise HTTPException(status_code=404, detail="Estimation with your id is already exists")
    new_estimation = Estimation(
        route_id=estimator_data.route_id,
        estimation_value=estimator_data.estimation,
        user_id=user_id,
        estimator_id=route.user_id,
        datetime=datetime.datetime.now()
    )
    db.add(new_estimation)
    db.commit()
    db.refresh(new_estimation)
    return new_estimation


@app.get("/routes/estimations/{route_id}")
def get_estimation_by_route_id(user_id: int, route_id: int, db: Session = Depends(get_db)):
    estimations = db.query(Estimation).filter(Estimation.route_id == route_id).all()
    if estimations:
        len_estimations = len(estimations)
        average_value = sum([estimation.estimation_value for estimation in estimations]) / len_estimations
        users_estimation = [estimation for estimation in estimations if estimation.user_id == user_id]
        return {
            "estimations": estimations, "average_value": average_value, "len_estimations": len_estimations,
            "users_estimation": users_estimation
        }
    return {"message": f"No estimations to this route {route_id}"}


@app.put("/routes/estimations/{route_id}")
def update_coordinate_point(estimator_id: int, route_id: int, estimation_value: float, db: Session = Depends(get_db)):
    estimation = db.query(Estimation).filter(
        Estimation.route_id == route_id, Estimation.estimator_id == estimator_id
    ).first()
    if estimation:
        estimation.estimation_value = estimation_value
        estimation.datetime = datetime.datetime.now()
        db.commit()
        db.refresh(estimation)
        return {"message": f"Success", "putted estimation": estimation}
    raise HTTPException(status_code=404, detail="Estimations with your id not found")


@app.delete("/routes/estimations/{route_id}")
def delete_estimation(estimator_id: int, route_id: int, db: Session = Depends(get_db)):
    estimation = db.query(Estimation).filter(
        Estimation.route_id == route_id, Estimation.estimator_id == estimator_id
    ).first()
    if estimation:
        db.delete(estimation)
        db.refresh(estimation)
        db.commit()
        return {"message": f"Success", "deleted estimation": estimation}
    raise HTTPException(status_code=404, detail="Estimations with your id not found")
