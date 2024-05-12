import datetime
from geopy.distance import great_circle as GC
from geopy.geocoders import Nominatim
from fastapi import FastAPI, Depends
from sqlalchemy import func
from fastapi.middleware.cors import CORSMiddleware
from PPgroup5.pythonBackEnd.auth.auth import router
from PPgroup5.pythonBackEnd.auth.schemas import is_valid_email
from PPgroup5.pythonBackEnd.auth.tokens_hashs import creating_hash_salt
from PPgroup5.pythonBackEnd.models.models import MyUserIn, Coordinate_get, OtherUserOut, MyUserOut, \
    RouteGet, EstimationGet
from PPgroup5.pythonBackEnd.auth.database import User, Route, Coordinate, Estimation, get_db, Session
from PPgroup5.pythonBackEnd.schemas.schemas import has_not_permission_error, not_found_error

app = FastAPI(title='Veloapp')
app.include_router(router)

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "DELETE", "PATCH", "PUT"],
    allow_headers=["*"],
)

@app.get("/")
def get_all(session: Session = Depends(get_db)):
    # получить последние роуты из ДБ и их среднюю оценку
    try:
        routes = session.query(Route).filter(Route.user_id != 0).all()[-10:]
    except:
        routes = session.query(Route).filter(Route.user_id != 0).all()
    avg_estimations = dict()
    for route in routes:
        estimations = session.query(Estimation).filter(Estimation.route_id == route.route_id).all()
        if estimations:
            len_estimations = len(estimations)
            average_value = sum([estimation.estimation_value for estimation in estimations]) / len_estimations
            avg_estimations[str(route.route_id)] = average_value
            break
        avg_estimations[str(route.route_id)] = None
    return {"status": "success",
            "data": {
                "routes": routes,
                "avg_estimations": avg_estimations
            },
            "details": None
            }


@app.get("/users/me")
def get_user_by_id(user_id: int, session: Session = Depends(get_db)):
    # мой профиль
    user = session.query(User).filter(User.id == user_id).first()
    routes = session.query(Route).filter(Route.user_id == user_id).all()
    coordinates = session.query(Coordinate).filter(Coordinate.user_id == user_id).all()
    estimations = session.query(Estimation).filter(Estimation.estimator_id == user_id).all()
    not_found_error(user, "User")
    return {"status": "success",
            "data": {
                "user": MyUserOut(
                    id=user_id,
                    name=user.name,
                    email=user.email,
                    telephone_number=user.telephone_number,
                    surname=user.surname,
                    patronymic=user.patronymic,
                    location=user.location,
                    sex=user.sex,
                    token_mobile=user.token_mobile
                ),
                "routes": routes,
                "coordinates": coordinates,
                "estimations": estimations
            },
            "details": None
            }


@app.get("/users/{user_id}")
def get_user_by_id(user_id: int, session: Session = Depends(get_db)):
    # профиль другого пользователя
    user = session.query(User).filter(User.id == user_id).first()
    routes = session.query(Route).filter(Route.user_id == user_id).all()
    coordinates = session.query(Coordinate).filter(Coordinate.user_id == user_id).all()
    estimations = session.query(Estimation).filter(Estimation.estimator_id == user_id).all()
    not_found_error(user, "User")
    return {"status": "success",
            "data": {
                "user": OtherUserOut(
                    id=user.id,
                    name=user.name,
                    surname=user.surname,
                    patronymic=user.patronymic,
                    location=user.location,
                    sex=user.sex
                ),
                "routes": routes,
                "coordinates": coordinates,
                "estimations": estimations

            },
            "details": None
            }


@app.put("/users/me/change")
def update_user(user_id: int, user_data: MyUserIn, permission: bool = False, session: Session = Depends(get_db)):
    has_not_permission_error(permission)
    user = session.query(User).filter(User.id == user_id).first()
    not_found_error(user, "User")
    generated_salt, hashed_password = creating_hash_salt(user_data.password)
    if not is_valid_email(user_data.email):
        user_data.email = None
    user_data_dict = user_data.dict()
    del user_data_dict["password"]
    user_data_dict["hashed_password"] = hashed_password
    user_data_dict["salt_hashed_password"] = generated_salt
    for attr, value in user_data_dict.items():
        setattr(user, attr, value)
    session.commit()
    return {"status": "success",
            "data": MyUserOut(
                id=user_id,
                name=user.name,
                email=user.email,
                telephone_number=user.telephone_number,
                surname=user.surname,
                patronymic=user.patronymic,
                location=user.location,
                sex=user.sex,
                token_mobile=user.token_mobile
            ),
            "details": None
            }


@app.delete("/users/me/change")
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


@app.get("/route/{route_id}")
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


@app.put("/route/{route_id}")
def update_route(user_id: int, route_id: int, route_data: RouteGet, permission: bool = False,
                 session: Session = Depends(get_db)):
    has_not_permission_error(permission)
    route = session.query(Route).filter(Route.route_id == route_id).first()
    not_found_error(route, "Route")

    route.distance = route_data.distance
    route.travel_time = route_data.travel_time
    route.comment = route_data.comment
    route.operation_time = datetime.datetime.now()
    session.commit()
    return {
        "status": "success",
        "data": {
            "route_id": route.route_id,
            "user_id": route.user_id,
            "distance": route.distance,
            "travel_time": route.travel_time,
            "comment": route.comment,
            "operation_time": route.operation_time
        },
        "details": None
    }


@app.delete("/route/{route_id}")
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
    not_found_error(user, "Token_mobile")
    return {"status": "success",
            "data": MyUserOut(
                id=user.id,
                name=user.name,
                email=user.email,
                telephone_number=user.telephone_number,
                surname=user.surname,
                patronymic=user.patronymic,
                location=user.location,
                sex=user.sex,
                token_mobile=user.token_mobile
            ),
            "details": None
            }


# coordinates
@app.get("/coordinates")
def get_coordinates_by_cord_id(user_id: int, permission: bool = False, session: Session = Depends(get_db)):
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
def create_coordinate_point(user_id: int, route_id: int, coordinate_data: Coordinate_get, session: Session = Depends(get_db)):
    # координаты привязаны к конкретным маршрутам, не создастся без маршрута
    user = session.query(User).filter(User.id == user_id).first()
    not_found_error(user, "User")
    route = session.query(Route).filter(Route.route_id == route_id).first()
    not_found_error(route, "Route")
    new_coordinate = Coordinate(
        user_id=user_id,
        route_id=route_id,
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
        "data": None,
        "details": None
    }


# estimations
@app.post("/routes/{route_id}/estimation")
def create_estimation(user_id: int, estimator_data: EstimationGet, session: Session = Depends(get_db)):
    route = session.query(Route).filter(Route.route_id == estimator_data.route_id).first()
    not_found_error(route, "Route")
    new_estimation = Estimation(
        route_id=estimator_data.route_id,
        estimation_value=estimator_data.estimation,
        estimator_id=user_id,
        comment=estimator_data.comment,
        datetime=datetime.datetime.now()
    )
    session.add(new_estimation)
    session.commit()
    return {
        "status": "success",
        "data": {
            "estimator_id": new_estimation.estimator_id,
            "route_id": new_estimation.route_id,
            "estimation_id": new_estimation.estimation_id,
            "estimation_value": new_estimation.estimation_value,
            "datetime": new_estimation.datetime,
            "comment": new_estimation.comment
        },
        "details": None
    }


@app.get("/routes/{route_id}/estimations")
def get_estimation_by_route_id(user_id: int, route_id: int, session: Session = Depends(get_db)):
    estimations = session.query(Estimation).filter(Estimation.route_id == route_id).all()
    not_found_error(estimations, "Estimations")
    len_estimations = len(estimations)
    average_value = sum([estimation.estimation_value for estimation in estimations]) / len_estimations
    my_estimation = [estimation for estimation in estimations if estimation.estimator_id == user_id]
    return {
        "status": "success",
        "data": {
            "estimations": estimations,
            "average_value": average_value,
            "len_estimations": len_estimations,
            "my_estimation": my_estimation
        },
        "details": None
    }


@app.put("/routes/{route_id}/estimation/{estimation.estimation_id}")
def update_estimation(estimator_id: int, route_id: int, estimation_value: float, permission: bool = False,
                            session: Session = Depends(get_db)):
    has_not_permission_error(permission)
    estimation = session.query(Estimation).filter(
        Estimation.route_id == route_id, Estimation.estimator_id == estimator_id).first()
    not_found_error(estimation, "Estimation")
    estimation.estimation_value = estimation_value
    estimation.datetime = datetime.datetime.now()
    session.commit()
    session.refresh(estimation)
    return {
        "status": "success",
        "data": {
            "estimation": estimation
        },
        "details": None
    }


@app.delete("/routes/{route_id}/estimation/{estimation.estimation_id}")
def delete_estimation(estimation_id: int, permission: bool = False, session: Session = Depends(get_db)):
    has_not_permission_error(permission)
    estimation = session.query(Estimation).filter(Estimation.estimation_id == estimation_id).first()
    not_found_error(estimation, "Estimation")
    session.delete(estimation)
    session.commit()
    return {
        "status": "success",
        "data": None,
        "details": None
    }
