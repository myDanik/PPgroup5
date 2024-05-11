import datetime
from geopy.distance import great_circle as GC
from geopy.geocoders import Nominatim
from fastapi import FastAPI, Depends
from sqlalchemy import func
from starlette.middleware.cors import CORSMiddleware

from PPgroup5.pythonBackEnd.auth.auth import router
from PPgroup5.pythonBackEnd.auth.schemas import is_login, error_login_telephone_userexists, \
    error_login_email_userexists, error_login_udentified, is_valid_email
from PPgroup5.pythonBackEnd.auth.tokens_hashs import creating_hash_salt
from PPgroup5.pythonBackEnd.models.models import UserDB, Coordinate_get, Estimation_get
from PPgroup5.pythonBackEnd.auth.database import User, Route, Coordinate, Estimation, get_db, Session
from PPgroup5.pythonBackEnd.schemas.schemas import has_not_permission_error, not_found_error

app = FastAPI(title='Veloapp')
app.include_router(router)

origins = [
    "http://localhost:8080"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/users/{user_id}")
def get_user_by_id(user_id: int, session: Session = Depends(get_db)):
    user = session.query(User).filter(User.id == user_id).first()
    not_found_error(user, "User")
    return {"status": "success",
            "data": {
                "user": user
            },
            "details": None
            }


@app.put("/users/{user_id}")
def update_user(user_id: int, user_data: UserDB, permission: bool = False, session: Session = Depends(get_db)):
    has_not_permission_error(permission)
    user = session.query(User).filter(User.id == user_id).first()
    not_found_error(user, "User")
    telephone_number, email, _ = is_login(user_data.login, error_login_telephone_userexists,
                                          error_login_email_userexists, error_login_udentified)

    generated_salt, hashed_password = creating_hash_salt(user_data.password)

    del user_data["password"]
    user_data["hashed_password"] = hashed_password
    user_data["salt_hashed_password"] = generated_salt
    for attr, value in user_data.items():
        setattr(user, attr, value)
    session.commit()
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
def delete_user(user_id: int, permission: bool = False, session: Session = Depends(get_db)):
    has_not_permission_error(permission)
    user = session.query(User).filter(User.id == user_id).first()
    not_found_error(user, "User")

    session.query(Estimation).filter(Estimation.estimator_id == user_id).update({'estimator_id': 0})
    session.query(Estimation).filter(Estimation.user_id == user_id).update({'user_id': 0})
    session.query(Coordinate).filter(Coordinate.user_id == user_id).update({'user_id': 0})
    session.query(Route).filter(Route.user_id == user_id).update({'user_id': 0})
    session.delete(user)
    session.commit()
    return {
        "status": "success",
        "data": None,
        "details": None
    }


@app.get("/users_info/{user_id}")
def get_user(user_id: int, route_id: int = None, session: Session = Depends(get_db)):
    user = session.query(User).filter(User.id == user_id).first()
    not_found_error(user, "User")
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
    return {
        "status": "success",
        "data": {
            "id": user.id,
            "name": user.name,
            "routes": route_by_id
        },
        "details": None
    }


@app.get("/route_info/{route_id}")
def get_route(route_id: int, session: Session = Depends(get_db)):
    route = session.query(Route).filter(Route.route_id == route_id).first()
    not_found_error(route, "Route")
    coordinates = session.query(Coordinate).filter(Coordinate.route_id == route_id).all()
    not_found_error(coordinates, "coordinates")
    geoLoc = Nominatim(user_agent="GetLoc")
    locnames = []
    for coord in coordinates:
        latitude_str = str(coord.latitude)
        longitude_str = str(coord.longitude)
        locname = geoLoc.reverse(f"{latitude_str}, {longitude_str}")
        locnames.append(str(locname) if locname else "")
    return {
        "status": "success",
        "data": {"route": route,
                 "coordinates": coordinates,
                 "locnames": locnames},
        "details": None
    }


@app.put("/users/{user_id}")
def update_user(user_id: int, user_data: UserDB, permission: bool = False, session: Session = Depends(get_db)):
    has_not_permission_error(permission)
    user = session.query(User).filter(User.id == user_id).first()
    not_found_error(user, "User")
    if session.query(User).filter(User.telephone_number == user_data.telephone_number).first():
        user_data.telephone_number = user.telephone_number
    if session.query(User).filter(User.email == user_data.email).first() or (not is_valid_email(user_data.email)):
        user_data.email = user.email
    generated_salt, hashed_password = creating_hash_salt(user_data.password)

    setattr(user, "hashed_password", hashed_password)
    setattr(user, "salt_hashed_password", generated_salt)
    for attr, value in user_data.dict(exclude_unset=True, exclude={"password"}).items():
        setattr(user, attr, value)
    session.commit()
    return {"status": "success",
            "data": user,
            "details": None
            }


@app.delete("/route/")
def delete_route(route_id: int, permission: bool = False, session: Session = Depends(get_db)):
    has_not_permission_error(permission)
    route = session.query(Route).filter(Route.route_id == route_id).first()
    not_found_error(route, "Route")
    session.query(Estimation).filter(Estimation.route_id == route_id).delete()
    session.query(Coordinate).filter(Coordinate.route_id == route_id).delete()
    session.delete(route)
    session.commit()
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
def check_token(token_mobile: str, session: Session = Depends(get_db)):
    user = session.query(User).filter(User.token_mobile == token_mobile).first()
    not_found_error(user, "User")
    return {
        "status": "success",
        "data": user,
        "details": None
    }


# coordinates
@app.get("/coordinates")
def get_coordinates_by_id(user_id: int, permission: bool = False, session: Session = Depends(get_db)):
    has_not_permission_error(permission)
    coordinates = session.query(Coordinate).filter(Coordinate.user_id == user_id).all()
    not_found_error(coordinates, "Coordinates")
    return {
        "status": "success",
        "data": {
            "coordinates": coordinates
        },
        "details": None
    }


@app.post("/coordinate/")
def create_coordinate_point(user_id: int, coordinate_data: Coordinate_get, session: Session = Depends(get_db)):
    user = session.query(User).filter(User.id == user_id).first()
    not_found_error(user, "User")
    new_coordinate = Coordinate(
        user_id=user_id,
        latitude=coordinate_data.latitude,
        longitude=coordinate_data.longitude,
        operation_time=datetime.datetime.now()
    )
    session.add(new_coordinate)
    session.commit()
    session.refresh(new_coordinate)
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


@app.put("/coordinate/{coordinate.cord_id")
def update_coordinate_point(user_id: int, cord_id: int, coordinate_data: Coordinate_get, permission: bool = False,
                            session: Session = Depends(get_db)):
    has_not_permission_error(permission)
    user = session.query(User).filter(User.id == user_id).first()
    not_found_error(user, "User")
    coordinate = session.query(Coordinate).filter(Coordinate.cord_id == cord_id).first()
    not_found_error(coordinate, "Coordinate")
    coordinate.latitude = coordinate_data.latitude
    coordinate.longitude = coordinate_data.longitude
    coordinate.operation_time = datetime.datetime.now()
    session.commit()
    session.refresh(user)
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
def delete_coordinate_point(user_id: int, cord_id: int, permission: bool = False, session: Session = Depends(get_db)):
    has_not_permission_error(permission)
    user = session.query(User).filter(User.id == user_id).first()
    not_found_error(user, "User")
    coordinate = session.query(Coordinate).filter(Coordinate.cord_id == cord_id).first()
    not_found_error(coordinate, "Coordinate")
    session.delete(coordinate)
    session.commit()
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
@app.post("/routes/{route_id}/estimation")
def create_estimation(user_id: int, estimator_data: Estimation_get, session: Session = Depends(get_db)):
    route = session.query(Route).filter(Route.route_id == estimator_data.route_id).first()
    not_found_error(route, "Route")
    user = session.query(Estimation).filter(Estimation.user_id == user_id).first()
    not_found_error(user, "User")
    new_estimation = Estimation(
        route_id=estimator_data.route_id,
        estimation_value=estimator_data.estimation,
        user_id=user_id,
        estimator_id=route.user_id,
        datetime=datetime.datetime.now()
    )
    session.add(new_estimation)
    session.commit()
    session.refresh(new_estimation)
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


@app.get("/routes/{route_id}/estimations")
def get_estimation_by_route_id(user_id: int, route_id: int, session: Session = Depends(get_db)):
    estimations = session.query(Estimation).filter(Estimation.route_id == route_id).all()
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


@app.put("/routes/{route_id}/estimation/{estimation.estimation_id}")
def update_coordinate_point(estimator_id: int, route_id: int, estimation_value: float, permission: bool = False,
                            session: Session = Depends(get_db)):
    has_not_permission_error(permission)
    estimation = session.query(Estimation).filter(
        Estimation.route_id == route_id, Estimation.estimator_id == estimator_id
    ).first()
    not_found_error(estimation, "Estimation")
    estimation.estimation_value = estimation_value
    estimation.datetime = datetime.datetime.now()
    session.commit()
    session.refresh(estimation)
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


@app.delete("/routes/{route_id}/estimation/{estimation.estimation_id}")
def delete_estimation(estimation_id: int, route_id: int, permission: bool = False, session: Session = Depends(get_db)):
    has_not_permission_error(permission)
    estimation = session.query(Estimation).filter(
        Estimation.route_id == route_id, Estimation.estimation_id == estimation_id).first()
    not_found_error(estimation, "Estimation")
    session.delete(estimation)
    session.refresh(estimation)
    session.commit()
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
