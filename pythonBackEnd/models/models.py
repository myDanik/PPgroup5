from typing import Optional, Union, List
from pydantic import BaseModel, Field


class RouteDB(BaseModel):
    """
    Модель маршрута в базе данных.

    Поля:
    - id: Идентификатор маршрута (необязательно).
    - latitude: Широта местоположения.
    - longitude: Долгота местоположения.
    - user_id: Идентификатор пользователя, связанного с маршрутом.
    """
    id: Optional[int] = None
    latitude: float
    longitude: float
    user_id: int


class MyUserIn(BaseModel):
    """
    Модель входных данных о текущем пользователе.

    Поля:
    - user_id (int): Идентификатор пользователя.
    - name (Optional[str]): Имя пользователя (необязательно).
    - email (Optional[str]): Электронная почта пользователя (необязательно).
    - telephone_number (Optional[str]): Номер телефона пользователя (необязательно).
    - surname (Optional[str]): Фамилия пользователя (необязательно).
    - patronymic (Optional[str]): Отчество пользователя (необязательно).
    - location (Optional[str]): Местоположение пользователя (необязательно).
    - sex (Optional[bool]): Пол пользователя (необязательно).
    - token_mobile (str): Токен мобильного приложения.
    """
    id: Optional[int] = None
    name: Optional[str] = None
    email: Optional[str] = None
    telephone_number: Optional[str] = None
    surname: Optional[str] = None
    patronymic: Optional[str] = None
    location: Optional[str] = None
    sex: Optional[str] = None
    birth: Optional[str] = None
    token_mobile: Optional[str] = None


class MyUserOut(BaseModel):
    """
    Модель исходящих данных о текущем пользователе.

    Поля:
    - id: Идентификатор пользователя.
    - name: Имя пользователя.
    - email: Электронная почта пользователя.
    - telephone_number: Номер телефона пользователя.
    - surname: Фамилия пользователя.
    - patronymic: Отчество пользователя.
    - location: Местоположение пользователя.
    - sex: Пол пользователя.
    - token_mobile: Мобильный токен пользователя.
    """
    id: int
    name: str
    email: Optional[str] = None
    telephone_number: Optional[str] = None
    surname: Optional[str] = None
    patronymic: Optional[str] = None
    location: Optional[str] = None
    sex: Optional[str] = None
    birth: Optional[str] = None
    token_mobile: Optional[str] = None


class OtherUserOut(BaseModel):
    """
    Модель исходящих данных о другом пользователе.

    Поля:
    - id: Идентификатор пользователя.
    - name: Имя пользователя.
    - surname: Фамилия пользователя.
    - patronymic: Отчество пользователя.
    - location: Местоположение пользователя.
    - sex: Пол пользователя.
    """
    id: int
    name: str
    surname: Optional[str] = None
    patronymic: Optional[str] = None
    location: Optional[str] = None
    sex: Optional[bool] = None


class RouteGet(BaseModel):
    """
    Модель используется для получения информации о маршруте.

    Поля:
    users_travel_time (int): Время путешествия пользователей по маршруту в секнудах.
    comment (str): Комментарий к маршруту.
    """
    users_travel_time: Optional[int] = None
    comment: Optional[str] = None


class RouteOut(BaseModel):
    # """
    # Модель используется для получения информации о маршруте.
    #
    # Поля:
    # users_travel_time (int): Время путешествия пользователей по маршруту в секнудах.
    # comment (str): Комментарий к маршруту.
    # """
    id: int
    users_travel_time: str
    comment: Optional[str] = None
    route_id: int
    user_id: int
    distance: Optional[float] = None
    avg_estimation: Optional[float] = None
    avg_travel_time_on_foot: Optional[float] = None
    avg_travel_velo_time: Optional[float] = None
    user_name: Optional[str]


class CoordinateGet(BaseModel):
    """
    Модель используется для ввода координат маршрута.

    Поля:
    latitude (float): Широта. Значение должно быть от -90.0 до 90.0.
    longitude (float): Долгота. Значение должно быть от -180.0 до 180.0.
    """
    latitude: float = Field(nullable=False, ge=-90.0, le=90.0)
    longitude: float = Field(nullable=False, ge=-180.0, le=180.0)


class EstimationGet(BaseModel):
    """
    Модель используется ввода оценки маршрута.

    Поля:
    route_id (int): Идентификатор маршрута.
    estimation (float): Оценка маршрута. Значение должно быть от 1 до 5.
    comment (str): Комментарий к оценке.
    """
    route_id: int
    estimation: float = Field(le=5, ge=1)
    comment: str
