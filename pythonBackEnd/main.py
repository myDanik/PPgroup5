import datetime
from geopy.distance import great_circle as GC
from geopy.geocoders import Nominatim
from datetime import timedelta
from fastapi import FastAPI, HTTPException, Depends
from PPgroup5.pythonBackEnd.auth.tokens_hashs import (creating_hash_salt, authenticate_user, create_token, token_user,
                                                      generate_token)
from PPgroup5.pythonBackEnd.models import (UserDB, User_login, Coordinate_get, Estimation_get, UserGet, UserInfo,
                                           CoordinateInfo, EstimationInfo)
from sqlalchemy import func, DateTime
from sqlalchemy.orm import sessionmaker
from PPgroup5.pythonBackEnd.auth.database import User, Route, Coordinate, engine, Estimation
from PPgroup5.pythonBackEnd.auth.schemas import Route_Data

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session = sessionmaker(engine)

app = FastAPI(title='Veloapp')


def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


@app.post("/authorization", response_model=UserGet)
def create_user(user_data: UserDB, db: Session = Depends(get_db)):
    if db.query(User).filter(User.login == user_data.login).first():
        raise HTTPException(status_code=409, detail={
            "status": "error",
            "data": None,
            "details": "Login is already exists"
        })
    generated_salt, hashed_password = creating_hash_salt(user_data.password)
    new_user = User(
        name=user_data.name,
        login=user_data.login,
        hashed_password=hashed_password,
        token_mobile=generate_token(),
        salt_hashed_password=generated_salt
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    entry_token = create_token(new_user.id, timedelta(hours=12))
    return {"status": "success",
            "data": {
                "entry_token": entry_token,
                "id": new_user.id,
                "name": new_user.name,
                "login": new_user.login,
                "token_mobile": new_user.token_mobile
            },
            "details": None
            }


@app.post("/login")
def login(login_user: User_login, entry_token: str = None, db: Session = Depends(get_db)):
    if token_user(entry_token):
        user_id = token_user(entry_token)
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                return {"status": "success",
                        "data": {
                            "entry_token": entry_token,
                            "id": user.id,
                            "name": user.name,
                            "login": user.login,
                            "token_mobile": user.token_mobile
                        },
                        "details": None
                    }
            raise HTTPException(status_code=404, detail={
                "status": "error",
                "data": None,
                "details": "Invalid token"
            })
    user = db.query(User).filter(User.login == login_user.login).first()
    if user:
        if authenticate_user(login_user.password, user.hashed_password, user.salt_hashed_password):
            entry_token = create_token(user.id, timedelta(hours=2))
            return {"status": "success",
                    "data": {
                        "entry_token": entry_token,
                        "id": user.id,
                        "name": user.name,
                        "login": user.login,
                        "token_mobile": user.token_mobile
                    },
                    "details": None
                    }
    raise HTTPException(status_code=404, detail={
        "status": "error",
        "data": None,
        "details": "Incorrect login or password"
    })


@app.get("/users/{user_id}", response_model=UserGet)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "data": None,
            "details": "User not found"
        })
    return {"status": "success",
            "data": {
                "id": user.id,
                "name": user.name,
                "login": user.login,
                "token_mobile": user.token_mobile
            },
            "details": None
            }


@app.put("/users/{user_id}", response_model=UserGet)
def update_user(user_id: int, user_data: UserDB, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "data": None,
            "details": "User not found"
        })
    generated_salt, hashed_password = creating_hash_salt(user_data.password)
    user_data = user_data.dict()
    del user_data["password"]
    user_data["hashed_password"] = hashed_password
    user_data["salt_hashed_password"] = generated_salt
    for attr, value in user_data.items():
        setattr(user, attr, value)
    db.commit()
    db.refresh(user)
    return {"status": "success",
            "data": {
                "id": user.id,
                "name": user.name,
                "login": user.login,
                "token_mobile": user.token_mobile
            },
            "details": None
            }


@app.delete("/users/{user_id}", response_model=UserGet)
def delete_user(user_id: int, permission: bool, db: Session = Depends(get_db)):
    if not permission:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "data": None,
            "details": "No permission"
        })
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "data": None,
            "details": "User not found"
        })
    db.delete(user)
    db.refresh(user)
    db.commit()
    # delete his routes
    return {"status": "success",
            "data": {
                "id": user.id,
                "name": user.name,
                "login": user.login,
                "token_mobile": user.token_mobile
            },
            "details": None
            }


@app.get("/users_info/{user_id}", response_model=UserInfo)
def get_user(user_id: int, route_id: int = None):
    session = Session()
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "data": None,
            "details": "User not found"
        })
    routes = session.query(Coordinate).filter((Coordinate.user_id == user_id)).all()
    if route_id is None:
        return {
            "status": "success",
            "data": {
                "id": user.id,
                "name": user.name,
                "routes": routes
            },
            "details": None
        }
    route_by_id = session.query(Coordinate).filter((Coordinate.user_id == user_id),
                                                   (Coordinate.route_id == route_id)).all()
    session.close()
    return {
        "status": "success",
        "data": {
            "id": user.id,
            "name": user.name,
            "routes": route_by_id
        },
        "details": None
    }


# не работает
@app.get("/route_info/{route_id}")
def get_route(route_id: int):
    session = Session()
    route = session.query(Route).filter(Route.route_id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    coordinates = session.query(Coordinate).filter(Coordinate.route_id == route_id).all()
    geoLoc = Nominatim(user_agent="GetLoc")
    locname = geoLoc.reverse(
        str(session.query(Coordinate.latitude).filter(Coordinate.route_id == route_id).first())[1:-2] + ", " + str(
            session.query(Coordinate.longitude).filter(Coordinate.route_id == route_id).first())[1:-2])
    session.close()
    return route, coordinates, str(locname)


@app.post("/route/")
def post_route(route_info: Route_Data):
    session = Session()
    user_id = session.query(User.id).filter(User.token == route_info.token).first()
    dist = 0
    for i in range(len(route_info.latitude_longitude_cordid) - 1):
        dist += GC((route_info.latitude_longitude_cordid[i][0], route_info.latitude_longitude_cordid[i][1]),
                   (route_info.latitude_longitude_cordid[i + 1][0], route_info.latitude_longitude_cordid[i + 1][1])).km
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
    return {"free_route_id": max_route_id + 1}


@app.get("/token_mobile/{token_mobile}", response_model=UserGet)
def check_token(token_mobile: str):
    session = Session()
    user = session.query(User).filter(User.token_mobile == token_mobile).first()
    if not user:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "data": None,
            "details": "User not found"
        })
    return {
        "status": "success",
        "data": {
            "id": user.id,
            "name": user.name,
            "login": user.login,
            "token_mobile": user.token_mobile
        },
        "details": None
    }


# coordinates
@app.get("/coordinates/{user_id}/", response_model=Coordinate)
def get_coordinates_by_id(user_id: int, db: Session = Depends(get_db)):
    coordinates = db.query(Coordinate).filter(Coordinate.user_id == user_id).all()
    if not coordinates:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "data": None,
            "details": "Coordinates not found"
        })
    return {
        "status": "success",
        "data": {
                "coordinates": coordinates
        },
        "details": None
    }


@app.post("/coordinates/{user_id}", response_model=CoordinateInfo)
def create_coordinate_point(user_id: int, coordinate_data: Coordinate_get, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "data": None,
            "details": "User not found"
        })
    new_coordinate = Coordinate(
        user_id=user_id,
        latitude=coordinate_data.latitude,
        longitude=coordinate_data.longitude,
        operation_time=datetime.datetime.now()
    )
    db.add(new_coordinate)
    db.commit()
    db.refresh(new_coordinate)
    return {
        "status": "success",
        "data": {
            "route_id": new_coordinate.route_id,
            "user_id": new_coordinate.user_id,
            "latitude": new_coordinate.latitude,
            "longitude": new_coordinate.longitude,
            "cord_id": new_coordinate.cord_id,
            "operation_time": new_coordinate.operation_time
        },
        "details": None
    }


@app.put("/coordinates/{user_id}", response_model=CoordinateInfo)
def update_coordinate_point(user_id: int, cord_id: int, coordinate_data: Coordinate_get, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "data": None,
            "details": "User not found"
        })
    coordinate = db.query(Coordinate).filter(Coordinate.cord_id == cord_id).first()
    if not coordinate:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "data": None,
            "details": "Coordinate not found"
        })
    coordinate.latitude = coordinate_data.latitude
    coordinate.longitude = coordinate_data.longitude
    coordinate.operation_time = datetime.datetime.now()
    db.commit()
    db.refresh(user)
    return {
        "status": "success",
        "data": {
            "route_id": coordinate.route_id,
            "user_id": coordinate.user_id,
            "latitude": coordinate.latitude,
            "longitude": coordinate.longitude,
            "cord_id": coordinate.cord_id,
            "operation_time": coordinate.operation_time
        },
        "details": None
    }


@app.delete("/coordinate/{cord_id}", response_model=CoordinateInfo)
def delete_coordinate_point(user_id: int, cord_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "data": None,
            "details": "User not found"
        })
    coordinate = db.query(Coordinate).filter(Coordinate.cord_id == cord_id).first()
    if not coordinate:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "data": None,
            "details": "Coordinate not found"
        })
    db.delete(coordinate)
    db.refresh(coordinate)
    db.commit()
    return {
        "status": "success",
        "data": {
            "route_id": coordinate.route_id,
            "user_id": coordinate.user_id,
            "latitude": coordinate.latitude,
            "longitude": coordinate.longitude,
            "cord_id": coordinate.cord_id,
            "operation_time": coordinate.operation_time
        },
        "details": None
    }


# estimations
@app.post("/routes/estimations/{route_id}", response_model=EstimationInfo)
def create_estimation(user_id: int, estimator_data: Estimation_get, db: Session = Depends(get_db)):
    route = db.query(Route).filter(Route.route_id == estimator_data.route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "data": None,
            "details": "Route not found"
        })
    user = db.query(Estimation).filter(Estimation.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "data": None,
            "details": "User not found"
        })
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
    return {
        "status": "success",
        "data": {
            "estimator_id": new_estimation.estimator_id,
            "route_id": new_estimation.route_id,
            "user_id": new_estimation.user_id,
            "estimation_id": new_estimation.estimation_id,
            "estimation_value": new_estimation.estimation_value,
            "datetime": new_estimation.datetime
        },
        "details": None
    }


@app.get("/routes/estimations/{route_id}")
def get_estimation_by_route_id(user_id: int, route_id: int, db: Session = Depends(get_db)):
    estimations = db.query(Estimation).filter(Estimation.route_id == route_id).all()
    if not estimations:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "data": None,
            "details": f"No estimations to this route {route_id}"
        })
    len_estimations = len(estimations)
    average_value = sum([estimation.estimation_value for estimation in estimations]) / len_estimations
    users_estimation = [estimation for estimation in estimations if estimation.user_id == user_id]
    return {
        "status": "success",
        "data": {
            "estimations": estimations,
            "average_value": average_value,
            "len_estimations": len_estimations,
            "users_estimation": users_estimation
        },
        "details": None
    }


@app.put("/routes/estimations/{route_id}", response_model=EstimationInfo)
def update_coordinate_point(estimator_id: int, route_id: int, estimation_value: float, db: Session = Depends(get_db)):
    estimation = db.query(Estimation).filter(
        Estimation.route_id == route_id, Estimation.estimator_id == estimator_id
    ).first()
    if not estimation:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "data": None,
            "details": "Estimation not found"
        })
    estimation.estimation_value = estimation_value
    estimation.datetime = datetime.datetime.now()
    db.commit()
    db.refresh(estimation)
    return {
        "status": "success",
        "data": {
            "estimator_id": estimation.estimator_id,
            "route_id": estimation.route_id,
            "user_id": estimation.user_id,
            "estimation_id": estimation.estimation_id,
            "estimation_value": estimation.estimation_value,
            "datetime": estimation.datetime
        },
        "details": None
    }


@app.delete("/routes/estimations/{route_id}", response_model=EstimationInfo)
def delete_estimation(estimator_id: int, route_id: int, db: Session = Depends(get_db)):
    estimation = db.query(Estimation).filter(
        Estimation.route_id == route_id, Estimation.estimator_id == estimator_id
    ).first()
    if not estimation:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "data": None,
            "details": "Estimation not found"
        })
    db.delete(estimation)
    db.refresh(estimation)
    db.commit()
    return {
        "status": "success",
        "data": {
            "estimator_id": estimation.estimator_id,
            "route_id": estimation.route_id,
            "user_id": estimation.user_id,
            "estimation_id": estimation.estimation_id,
            "estimation_value": estimation.estimation_value,
            "datetime": estimation.datetime
        },
        "details": None
    }
