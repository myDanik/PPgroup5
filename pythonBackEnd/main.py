import datetime
from geopy.distance import great_circle as GC
from geopy.geocoders import Nominatim
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import func

from PPgroup5.pythonBackEnd.auth.auth import router
from PPgroup5.pythonBackEnd.auth.tokens_hashs import creating_hash_salt
from PPgroup5.pythonBackEnd.auth.models import UserDB, Coordinate_get, Estimation_get
from PPgroup5.pythonBackEnd.auth.database import User, Route, Coordinate, Estimation, get_db, Session
from PPgroup5.pythonBackEnd.schemas.schemas import Route_Data, has_not_permission_error, not_found_error

app = FastAPI(title='Veloapp')
app.include_router(router)


@app.get("/users/{user_id}")
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    not_found_error(user, "User")
    return {"status": "success",
            "data": {
                "id": user.id,
                "name": user.name,
                "login": user.login,
                "token_mobile": user.token_mobile
            },
            "details": None
            }


@app.put("/users/{user_id}")
def update_user(user_id: int, user_data: UserDB, permission: bool = False, db: Session = Depends(get_db)):
    has_not_permission_error(permission)
    user = db.query(User).filter(User.id == user_id).first()
    not_found_error(user, "User")
    if user.login == user_data.login:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "data": None,
            "details": "Login is already exists"
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


@app.delete("/users/{user_id}")
def delete_user(user_id: int, permission: bool = False, db: Session = Depends(get_db)):
    has_not_permission_error(permission)
    user = db.query(User).filter(User.id == user_id).first()
    not_found_error(user, "User")

    db.query(Estimation).filter(Estimation.estimator_id == user_id).update({'estimator_id': 0})
    db.query(Estimation).filter(Estimation.user_id == user_id).update({'user_id': 0})
    db.query(Coordinate).filter(Coordinate.user_id == user_id).update({'user_id': 0})
    db.query(Route).filter(Route.user_id == user_id).update({'user_id': 0})
    db.delete(user)
    db.commit()
    return {
        "status": "success",
        "data": None,
        "details": None
        }


@app.get("/users_info/{user_id}")
def get_user(user_id: int, route_id: int = None, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    not_found_error(user, "User")
    routes = db.query(Coordinate).filter((Coordinate.user_id == user_id)).all()
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
    route_by_id = db.query(Coordinate).filter((Coordinate.user_id == user_id),
                                                   (Coordinate.route_id == route_id)).all()
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
    not_found_error(route, "Route")
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


@app.delete("/route/")
def delete_route(route_id: int, permission: bool = False, db: Session = Depends(get_db)):
    has_not_permission_error(permission)
    route = db.query(Route).filter(Route.route_id == route_id).first()
    not_found_error(route, "Route")
    db.query(Estimation).filter(Estimation.route_id == route_id).delete()
    db.query(Coordinate).filter(Coordinate.route_id == route_id).delete()
    db.delete(route)
    db.commit()
    return {
        "status": "success",
        "data": None,
        "details": None
        }


@app.get("/free_route_id/")
def get_free_route_id():
    session = Session()
    max_route_id = session.query(func.max(Route.route_id)).scalar()
    return {"free_route_id": max_route_id + 1}


@app.get("/token_mobile/{token_mobile}")
def check_token(token_mobile: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.token_mobile == token_mobile).first()
    not_found_error(user, "User")
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
@app.get("/coordinates/{user_id}/")
def get_coordinates_by_id(user_id: int, permission: bool = False, db: Session = Depends(get_db)):
    has_not_permission_error(permission)
    coordinates = db.query(Coordinate).filter(Coordinate.user_id == user_id).all()
    not_found_error(coordinates, "Coordinates")
    return {
        "status": "success",
        "data": {
                "coordinates": coordinates
        },
        "details": None
    }


@app.post("/coordinates/{user_id}")
def create_coordinate_point(user_id: int, coordinate_data: Coordinate_get, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    not_found_error(user, "User")
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


@app.put("/coordinates/{user_id}")
def update_coordinate_point(user_id: int, cord_id: int, coordinate_data: Coordinate_get, permission: bool = False,
                            db: Session = Depends(get_db)):
    has_not_permission_error(permission)
    user = db.query(User).filter(User.id == user_id).first()
    not_found_error(user, "User")
    coordinate = db.query(Coordinate).filter(Coordinate.cord_id == cord_id).first()
    not_found_error(coordinate, "Coordinate")
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


@app.delete("/coordinate/{cord_id}")
def delete_coordinate_point(user_id: int, cord_id: int, permission: bool = False, db: Session = Depends(get_db)):
    has_not_permission_error(permission)
    user = db.query(User).filter(User.id == user_id).first()
    not_found_error(user, "User")
    coordinate = db.query(Coordinate).filter(Coordinate.cord_id == cord_id).first()
    not_found_error(coordinate, "Coordinate")
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
@app.post("/routes/estimations/{route_id}")
def create_estimation(user_id: int, estimator_data: Estimation_get, db: Session = Depends(get_db)):
    route = db.query(Route).filter(Route.route_id == estimator_data.route_id).first()
    not_found_error(route, "Route")
    user = db.query(Estimation).filter(Estimation.user_id == user_id).first()
    not_found_error(user, "User")
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
    not_found_error(estimations, "Estimations")
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


@app.put("/routes/estimations/{route_id}")
def update_coordinate_point(estimator_id: int, route_id: int, estimation_value: float, permission: bool = False,
                            db: Session = Depends(get_db)):
    has_not_permission_error(permission)
    estimation = db.query(Estimation).filter(
        Estimation.route_id == route_id, Estimation.estimator_id == estimator_id
    ).first()
    not_found_error(estimation, "Estimation")
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


@app.delete("/routes/estimations/{route_id}")
def delete_estimation(estimation_id: int, route_id: int, permission: bool = False, db: Session = Depends(get_db)):
    has_not_permission_error(permission)
    estimation = db.query(Estimation).filter(
        Estimation.route_id == route_id, Estimation.estimation_id == estimation_id).first()
    not_found_error(estimation, "Estimation")
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
