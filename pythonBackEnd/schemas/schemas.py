from geopy import Nominatim
from pydantic import BaseModel, validator, EmailStr
from typing import List
from fastapi import HTTPException

from PPgroup5.pythonBackEnd.database.database import User, session, Route, Coordinate


class Route_Data(BaseModel):
    """
    Модель данных маршрута.

    Поля:
    - travel_time: Время путешествия.
    - latitude_longitude: Список координат (широта и долгота).
    - token_mobile: Мобильный токен пользователя.
    """
    travel_time: int
    latitude_longitude: List[List[float]]
    token_mobile: str

    @validator('latitude_longitude', each_item=True)
    def check_list_length(cls, v):
        """
        Валидатор для проверки длины вложенного списка координат.

        Аргументы:
        - v: Список координат.

        Исключения:
        - HTTPException: Если длина списка не равна 2.
        """
        if len(v) != 2:
            raise HTTPException(status_code=404, detail={
                "status": "error",
                "data": None,
                "details": "len is not 2"
                })
        return v


def not_found_error(arg, name):
    """
    Функция для генерации ошибки, если объект не найден.

    Аргументы:
    - arg: Объект, который нужно проверить.
    - name: Имя объекта для отображения в сообщении об ошибке.

    Исключения:
    - HTTPException: Если объект не найден.
    """
    if not arg:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "data": None,
            "details": f"{name} not found"
        })


def user_search(user_id):
    """
    Функция для поиска пользователя по ID.

    Аргументы:
    - user_id: ID пользователя.

    Возвращает:
    - Пользователь (User) или вызывает ошибку, если пользователь не найден.
    """
    user = session.query(User).filter(User.id == user_id).first()
    not_found_error(user, "User")
    return user


def route_search(route_id):
    """
    Функция для поиска маршрута по ID.

    Аргументы:
    - route_id: ID маршрута.

    Возвращает:
    - Маршрут (Route) или вызывает ошибку, если маршрут не найден.
    """
    route = session.query(Route).filter(Route.route_id == route_id).first()
    not_found_error(route, "Route")
    return route


def coordinate_search(cord_id):
    """
    Функция для поиска координаты по ID.

    Аргументы:
    - cord_id: ID координаты.

    Возвращает:
    - Координата (Coordinate) или вызывает ошибку, если координата не найдена.
    """
    coordinate = session.query(Coordinate).filter(Coordinate.cord_id == cord_id).first()
    not_found_error(coordinate, "Coordinate")
    return coordinate


def get_lock_by_cords(latitude, longitude):
    """
    Функция для получения названия местоположения по координатам.

    Аргументы:
    - latitude: Широта.
    - longitude: Долгота.

    Возвращает:
    - Название местоположения или None, если местоположение не найдено.
    """
    try:
        geoLoc = Nominatim(user_agent="GetLoc")
        locname = geoLoc.reverse(f"{str(latitude)}, {str(longitude)}")
        return locname
    except:
        return


def time_redakt(time):
    """
    Функция для форматирования секунд в часы и минуты.

    Аргументы:
    - time: Время в секундах.

    Возвращает:
    - Время в формате Часы:Минуты:Секунды.
    """
    minutes = "0" + str((time % 3600) // 60)
    seconds = "0" + str(time % 60)
    return f"{time // 3600}:{minutes[-2:]}:{seconds[-2:]}"
