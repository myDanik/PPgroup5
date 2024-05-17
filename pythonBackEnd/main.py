import datetime
from random import shuffle
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import func
from fastapi.middleware.cors import CORSMiddleware
from PPgroup5.pythonBackEnd.auth.auth import router
from PPgroup5.pythonBackEnd.current_user.me import profile
from PPgroup5.pythonBackEnd.models.models import OtherUserOut, MyUserOut, EstimationGet
from PPgroup5.pythonBackEnd.database.database import User, Route, Coordinate, Estimation, get_db, Session
from PPgroup5.pythonBackEnd.schemas.schemas import has_not_permission_error, not_found_error


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
def get_routes(page: int = 1, session: Session = Depends(get_db)):
    # получить случайные роуты из БД и их среднюю оценку
    # добавить pages
    routes = session.query(Route).filter(Route.user_id != 0).all()
    shuffle(routes)
    random_routes = sorted(routes[-15:], key=lambda x: x.route_id)
    avg_estimations = dict()
    for route in random_routes:
        estimations = session.query(Estimation).filter(Estimation.route_id == route.route_id).all()
        if estimations:
            len_estimations = len(estimations)
            average_value = sum([estimation.estimation_value for estimation in estimations]) / len_estimations
            avg_estimations[str(route.route_id)] = average_value
        else:
            avg_estimations[str(route.route_id)] = None
    return {"status": "success",
            "data": {
                "routes": random_routes,
                "avg_estimations": avg_estimations
            },
            "details": None
            }


@app.get("/users/{user_id}")
def get_user_by_id(user_id: int, session: Session = Depends(get_db)):
    # профиль другого пользователя
    user = session.query(User).filter(User.id == user_id).first()
    not_found_error(user, "User")
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
    route = session.query(Route).filter(Route.route_id == route_id).first()
    not_found_error(route, "Route")
    coordinates = session.query(Coordinate).filter(Coordinate.route_id == route_id).all()
    not_found_error(coordinates, "coordinates")
    coordinates.sort(key=lambda x: x.order)
    is_favorite_route = None
    user = session.query(User).filter(User.id == user_id).first()
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


# @app.post("/route/{route_id}")
# def add_route_to_favorite(route_id: int, user_id: int, session: Session = Depends(get_db)):
#     user = session.query(User).filter(User.id == user_id).first()
#     not_found_error(user, "User")
#     route = session.query(Route).filter(Route.route_id == route_id).first()
#     not_found_error(route, "Route")
#     if route_id not in user.favorite_routes:
#         print("not in")
#         user.favorite_routes.append(route_id)
#         session.commit()
#     return {
#         "status": "success",
#         "data": None,
#         "details": None
#     }
@app.post("/route/{route_id}")
def add_route_to_favorite(route_id: int, user_id: int, session: Session = Depends(get_db)):
    user = session.query(User).filter(User.id == user_id).first()
    not_found_error(user, "User")
    route = session.query(Route).filter(Route.route_id == route_id).first()
    not_found_error(route, "Route")

    if route_id not in user.favorite_routes:
        user.favorite_routes = user.favorite_routes + [route_id]
        session.commit()
    return {
        "status": "success",
        "data": None,
        "details": None
    }


@app.delete("/route/{route_id}")
def remove_favorite_route(user_id: int, route_id: int, session: Session = Depends(get_db)):
    user = session.query(User).filter(User.id == user_id).first()
    not_found_error(user, "User")
    route = session.query(Route).filter(Route.route_id == route_id).first()
    not_found_error(route, "Route")

    if route_id in user.favorite_routes:
        user.favorite_routes.remove(route_id)
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

#по токену принять координаты в массиве вида [[longitude, latitude], [longitude, latitude],[longitude, latitude]]