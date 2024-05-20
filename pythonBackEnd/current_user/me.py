import datetime
from fastapi import APIRouter, Depends, HTTPException
from geopy.distance import great_circle as GC

from PPgroup5.pythonBackEnd.auth.schemas import is_valid_email, error_email_userexists, \
    error_telephone_userexists, is_telephone_number
from PPgroup5.pythonBackEnd.database.database import Session, get_db, User, Route, Coordinate, Estimation
from PPgroup5.pythonBackEnd.models.models import MyUserOut, MyUserIn, RouteGet, CoordinateGet
from PPgroup5.pythonBackEnd.schemas.schemas import not_found_error, get_lock_by_cords, route_search, user_search, \
    coordinate_search

profile = APIRouter(
    prefix="/me",
    tags=["current_user_profile"]
)


@profile.get("/profile")
def get_current_user(user_id: int, session: Session = Depends(get_db)):
    """
    Получение текущего профиля пользователя.

    Аргументы:
    - user_id: ID пользователя.
    - session: Сессия базы данных.

    Возвращает:
    - Данные профиля пользователя, включая его любимые маршруты и созданные им оценки и маршруты.
    """
    user = user_search(user_id)
    routes = session.query(Route).filter(Route.user_id == user_id).all()
    estimations = session.query(Estimation).filter(Estimation.estimator_id == user_id).all()
    if user.favorite_routes:
        favorite_routes = session.query(Route).filter(Route.route_id.in_(user.favorite_routes)).all()
    else:
        favorite_routes = []
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
                    token_mobile=user.token_mobile,
                    birth=user.birth
                ),
                "favorite_routes": favorite_routes,
                "routes": routes,
                "estimations": estimations
            },
            "details": None
            }


@profile.put("/profile")
def update_user(user_data: MyUserIn, session: Session = Depends(get_db)):
    """
    Обновление профиля пользователя.

    Аргументы:
    - user_data: Данные пользователя для обновления.
    - session: Сессия базы данных.

    Возвращает:
    - Обновленные данные профиля пользователя.

    Если приходит пустое значение, то данные сохраняются такими, какими были в базе данных.
    """
    user = session.query(User).filter(User.id == user_data.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_data.telephone_number:
        if not is_telephone_number(user_data.telephone_number):
            raise HTTPException(status_code=400, detail={
                "status": "error",
                "data": None,
                "details": "Bad telephone_number"
            })
        if session.query(User).filter(
            User.telephone_number == user_data.telephone_number,
            User.id != user_data.id
        ).first():
            raise HTTPException(status_code=400, detail="Telephone number already exists")

    if user_data.email:
        if not is_valid_email(user_data.email):
            print(user_data.email)
            raise HTTPException(status_code=400, detail={
                "status": "error",
                "data": None,
                "details": "Bad email"
            })
        if session.query(User).filter(
            User.email == user_data.email,
            User.id != user_data.id
        ).first():
            raise HTTPException(status_code=400, detail="Email already exists")

    user_data_dict = user_data.dict(exclude_unset=True)

    for attr, value in user_data_dict.items():
        if value is not None:
            setattr(user, attr, value)
    session.commit()
    session.refresh(user)

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
                token_mobile=user.token_mobile,
                birth=user.birth
            ),
            "details": None
            }

    # # if "password" in user_data_dict:
    # #     password = user_data_dict.pop("password")
    # #     generated_salt, hashed_password = creating_hash_salt(password)
    # #     user_data_dict["hashed_password"] = hashed_password
    # #     user_data_dict["salt_hashed_password"] = generated_salt


@profile.delete("/profile")
def delete_user(user_id: int, session: Session = Depends(get_db)):
    """
    Удаление профиля пользователя.

    Аргументы:
    - user_id: ID пользователя.
    - session: Сессия базы данных.

    Возвращает:
    - Статус успеха после удаления пользователя и связанных данных.
    """
    user = user_search(user_id)

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


@profile.post("/route")
def create_route(user_id: int, route_data: RouteGet, route_id: int = None, route_created: bool = False,
                 cancel: bool = False, session: Session = Depends(get_db)):
    if cancel and route_created:
        route = session.query(Route).filter(Route.user_id == user_id).order_by(Route.id.desc()).first()
        not_found_error(route, "Route")

        coordinates = session.query(Coordinate).filter(Coordinate.route_id == route.id).all()
        for coord in coordinates:
            session.delete(coord)
        session.delete(route)
        session.commit()

        return {
            "status": "success",
            "data": None,
            "details": "Route and associated coordinates have been deleted"
        }
    user_search(user_id)
    if not route_created:
        new_route = Route(user_id=user_id)
        session.add(new_route)
        session.commit()
        session.refresh(new_route)
        route_id = new_route.route_id
    coordinates = session.query(Coordinate).filter(Coordinate.route_id == route_id).all()
    if len(coordinates) < 2:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "data": {
                "route_id": route_id
            },
            "details": "Count of coordinates less than 2"
        })
    route = route_search(route_id)
    coordinates = list(map(lambda x: (x.latitude, x.longitude), sorted(coordinates, key=lambda x: x.order)))
    distances = []
    for index in range(len(coordinates) - 1):
        distances.append(GC(coordinates[index], coordinates[index + 1]).km)
    avg_travel_time_on_foot = round(sum(distances) / 6 * 3600, 0)
    avg_travel_velo_time = round(sum(distances) / 16.3 * 3600, 0)
    routes = session.query(Route).filter(Route.user_id == user_id).all()
    distance = [(route.distance, route.users_travel_time) for route in routes
                if route.distance is not None and route.users_travel_time is not None]
    if distance:
        users_avg_travel_time_predict = sum(list(map(lambda x, y: round(x/y, 0), distances)))
    else:
        users_avg_travel_time_predict = None

    route.distance = sum(distances),
    route.avg_travel_time_on_foot = avg_travel_time_on_foot
    route.avg_travel_velo_time = avg_travel_velo_time
    route.users_travel_time = route_data.users_travel_time
    route.comment = route_data.comment
    route.operation_time = datetime.datetime.now()

    session.commit()
    session.refresh(route)
    return {
        "status": "success",
        "data": {
            "route": route,
            "coordinates": coordinates,
            "distances": distances,
            "users_avg_travel_time_predict": users_avg_travel_time_predict
        },
        "details": None
    }


@profile.put("/route/{route_id}")
def update_route(route_id: int, route_data: RouteGet, session: Session = Depends(get_db)):
    """
    Обновление маршрута.

    Аргументы:
    - route_id: ID маршрута.
    - route_data: Данные маршрута для обновления.
    - session: Сессия базы данных.

    Возвращает:
    - Обновленные данные маршрута.
    """
    route = route_search(route_id)

    route_data_dict = route_data.dict(exclude_unset=True)

    for attr, value in route_data_dict.items():
        if value is not None:
            setattr(route, attr, value)
    route.operation_time = datetime.datetime.now()
    session.commit()
    session.refresh(route)
    return {
        "status": "success",
        "data": {
            "route": route
        },
        "details": None
    }


@profile.delete("/route/{route_id}")
def delete_route(route_id: int, session: Session = Depends(get_db)):
    route = route_search(route_id)
    session.query(Estimation).filter(Estimation.route_id == route_id).delete()
    session.query(Coordinate).filter(Coordinate.route_id == route_id).delete()
    session.delete(route)
    session.commit()
    return {
        "status": "success",
        "data": None,
        "details": None
    }


@profile.post("/route/{route_id}/coordinate/")
def create_coordinate(user_id: int, route_id: int, coordinate_data: CoordinateGet,
                      session: Session = Depends(get_db)):
    # координаты привязаны к конкретным маршрутам, не создастся без маршрута
    user_search(user_id)
    route = route_search(route_id)
    locname = get_lock_by_cords(coordinate_data.latitude, coordinate_data.longitude)
    new_coordinate = Coordinate(
        user_id=user_id,
        route_id=route.route_id,
        latitude=coordinate_data.latitude,
        longitude=coordinate_data.longitude,
        locname=str(locname) if locname else "",
        operation_time=datetime.datetime.now()
    )
    session.add(new_coordinate)
    session.commit()
    session.refresh(new_coordinate)
    return {
        # route_created запомнить как True
        "status": "success",
        "data": {
            "coordinate": new_coordinate,
        },
        "details": None
    }


# @profile.put("/route/{route_id}/coordinate/{cord_id}")
# def update_coordinate(cord_id: int, order: int, coordinate_data: CoordinateGet, session: Session = Depends(get_db)):
#     coordinate = session.query(Coordinate).filter(Coordinate.cord_id == cord_id).first()
#     not_found_error(coordinate, "Coordinate")
#
#     route_id = coordinate.route_id
#     old_order = coordinate.order
#
#     # Удаляем координату и обновляем порядок оставшихся координат
#     session.delete(coordinate)
#     session.commit()
#
#     remaining_coordinates = session.query(Coordinate).filter(
#         Coordinate.route_id == route_id,
#         Coordinate.order > old_order
#     ).all()
#     for coord in remaining_coordinates:
#         coord.order -= 1
#     session.commit()
#     # Проверяем и обновляем порядок для новой координаты
#     existing_coordinates = session.query(Coordinate).filter(
#         Coordinate.route_id == route_id,
#         Coordinate.order >= order
#     ).all()
#     locname = get_lock_by_cords(coordinate_data.latitude, coordinate_data.longitude)
#     for coord in existing_coordinates:
#         coord.order += 1
#     updated_coordinate = Coordinate(
#         cord_id=cord_id,  # Сохраняем тот же id для обновленной координаты
#         user_id=coordinate.user_id,
#         route_id=route_id,
#         latitude=coordinate_data.latitude,
#         longitude=coordinate_data.longitude,
#         order=order,
#         locname=str(locname) if locname else "",
#         operation_time=datetime.datetime.now()
#     )
#
#     session.add(updated_coordinate)
#     session.commit()
#     session.refresh(updated_coordinate)
#
#     return {
#         "status": "success",
#         "data": {
#             "coordinate": updated_coordinate
#         },
#         "details": None
#     }
#

@profile.delete("/route/{route_id}/coordinate/{cord_id}")
def delete_coordinate(cord_id: int, session: Session = Depends(get_db)):
    coordinate = coordinate_search(cord_id)
    session.delete(coordinate)
    session.commit()
    return {
        "status": "success",
        "data": None,
        "details": None
    }

