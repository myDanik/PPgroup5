import datetime
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import func
from geopy.distance import great_circle as GC

from fastapi.middleware.cors import CORSMiddleware
from PPgroup5.pythonBackEnd.auth.auth import router
from PPgroup5.pythonBackEnd.current_user.me import profile
from PPgroup5.pythonBackEnd.models.models import OtherUserOut, MyUserOut, EstimationGet, RouteOut
from PPgroup5.pythonBackEnd.database.database import User, Route, Coordinate, Estimation, get_db, Session
from PPgroup5.pythonBackEnd.schemas.schemas import not_found_error, Route_Data, user_search, route_search, time_redakt

app = FastAPI(title='Veloapp')
app.include_router(router)
app.include_router(profile)

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
def get_routes(session: Session = Depends(get_db)):
    # добавить pages
    routes = session.query(Route).filter(Route.user_id != 0).all()
    routes = sorted(routes[-15:], key=lambda x: x.route_id)
    routes_out = []
    id = 1
    for route in routes:
        estimations = session.query(Estimation).filter(Estimation.route_id == route.route_id).all()
        if estimations:
            len_estimations = len(estimations)
            avg_estimation = round(sum([estimation.estimation_value for estimation in estimations]) / len_estimations, 2)
        else:
            avg_estimation = None
        user = session.query(User).filter(User.id == route.user_id).first()
        user_name = user.name

        routes_out.append(
                RouteOut(
                    id=id,
                    users_travel_time=time_redakt(route.users_travel_time),
                    comment=route.comment,
                    route_id=route.route_id,
                    user_id=route.user_id,
                    distance=route.user_id,
                    avg_travel_time_on_foot=route.avg_travel_time_on_foot,
                    avg_travel_velo_time=route.avg_travel_velo_time,
                    avg_estimation=avg_estimation,
                    user_name=user_name
                        )
                    )
        id += 1
    return {"status": "success",
            "data": routes_out,
            "details": None
            }


@app.get("/users/{user_id}")
def get_user_by_id(user_id: int, session: Session = Depends(get_db)):
    # профиль другого пользователя
    user = user_search(user_id)
    routes = session.query(Route).filter(Route.user_id == user_id).all()
    coordinates = session.query(Coordinate).filter(Coordinate.user_id == user_id).all()
    estimations = session.query(Estimation).filter(Estimation.estimator_id == user_id).all()
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


@app.get("/route/{route_id}")
def get_route(route_id: int, user_id: int = None, session: Session = Depends(get_db)):
    user = user_search(user_id)
    route = route_search(route_id)
    coordinates = session.query(Coordinate).filter(Coordinate.route_id == route_id).all()
    not_found_error(coordinates, "coordinates")
    coordinates.sort(key=lambda x: x.order)
    is_favorite_route = None
    if user:
        is_favorite_route = route_id in user.favorite_routes
    return {
        "status": "success",
        "data": {"route": route,
                 "coordinates": coordinates,
                 "is_favorite_route": is_favorite_route
                 },
        "details": None
    }


@app.post("/route/{route_id}")
def add_remove_route_to_favorite(route_id: int, user_id: int, session: Session = Depends(get_db)):
    user = user_search(user_id)
    route_search(route_id)
    if user.favorite_routes is None:
        user.favorite_routes = [route_id]
    elif route_id not in user.favorite_routes:
        user.favorite_routes = user.favorite_routes + [route_id]
    else:
        user.favorite_routes = list(filter(lambda x: x != route_id, user.favorite_routes))
    session.commit()
    session.refresh(user)
    return {
        "status": "success",
        "data": {"user_favorite_routes": user.favorite_routes},
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
def update_estimation(estimator_id: int, route_id: int, estimation_value: float, session: Session = Depends(get_db)):
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
def delete_estimation(estimation_id: int, session: Session = Depends(get_db)):
    estimation = session.query(Estimation).filter(Estimation.estimation_id == estimation_id).first()
    not_found_error(estimation, "Estimation")
    session.delete(estimation)
    session.commit()
    return {
        "status": "success",
        "data": None,
        "details": None
    }


@app.post("/route/")
def post_route_arrow(route_info: Route_Data, session: Session = Depends(get_db)):
    user = session.query(User).filter(User.token_mobile == route_info.token_mobile).first()
    not_found_error(user, "User")

    dist = 0
    for i in range(len(route_info.latitude_longitude)-1):
        dist += GC((route_info.latitude_longitude[i][0], route_info.latitude_longitude[i][1]), (route_info.latitude_longitude[i+1][0], route_info.latitude_longitude[i+1][1])).km
    new_route = Route(user_id=user.id, distance=dist, travel_time=route_info.travel_time, operation_time=datetime.datetime.now())
    session.add(new_route)
    session.commit()
    session.refresh(new_route)
    for cord in range(len(route_info.latitude_longitude)):
        new_coordinate = Coordinate(route_id=new_route.route_id,
                                    user_id=user.id,
                                    latitude=route_info.latitude_longitude[cord][0],
                                    longitude=route_info.latitude_longitude[cord][1],
                                    operation_time=datetime.datetime.now())
        session.add(new_coordinate)
    session.commit()
    session.refresh(new_route)
    return {
        "status": "success",
        "data": {"route": new_route},
        "details": None
    }


@app.get("/route/{route_id}/distance")
def get_distance(route_id: int, session: Session = Depends(get_db)):
    route_search(route_id)
    coordinates = sorted(session.query(Coordinate).filter(Coordinate.route_id == route_id).all(), key=lambda x: x.cord_id)
    coordinates = list(map(lambda x: (x.latitude, x.longitude), coordinates))
    if len(coordinates) < 2:
        raise HTTPException(status_code=400, detail={
            "status": "error",
            "data": None,
            "details": "less than 2 coordinates"
        })
    distance = 0
    for index in range(len(coordinates) - 1):
        distance += GC(coordinates[index], coordinates[index + 1]).km
    return {
        "status": "success",
        "data": {"distance": distance},
        "details": None
    }


@app.post("/route/{route_id}/distance")
def post_distance(route_id: int, distance: float, session: Session = Depends(get_db)):
    route = session.query(Route).filter(Route.route_id == route_id).first()
    route.distance = distance
    session.commit()
    return {
        "status": "success",
        "data": {"distance": distance},
        "details": None
    }
