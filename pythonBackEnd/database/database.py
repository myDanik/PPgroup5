from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Boolean, ARRAY
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from PPgroup5.pythonBackEnd.pg import url

Base = declarative_base()
engine = create_engine(url)
# Создание сессии для работы с базой данных
Session = sessionmaker(engine)
session = Session()


# Функция для получения сессии базы данных, которая автоматически закрывает сессию после использования
def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


# Модель пользователя
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)  # Имя пользователя
    email = Column(String)  # Email пользователя
    telephone_number = Column(String)  # Номер телефона пользователя
    surname = Column(String)  # Фамилия пользователя
    patronymic = Column(String)  # Отчество пользователя
    location = Column(String)  # Местоположение пользователя (город проживания)
    sex = Column(String)  # Пол пользователя (male = мужчина, female = женщина)
    favorite_routes = Column(ARRAY(Integer), default=[])  # Список избранных маршрутов в виде [cord_id1, cord_id2]
    hashed_password = Column(String, nullable=False)  # Хэшированный пароль пользователя
    salt_hashed_password = Column(String, nullable=False)  # Соль для хэширования пароля
    token_mobile = Column(String, nullable=False)  # Токен мобильного приложения
    authorizated_at = Column(DateTime)  # Время авторизации пользователя
    birth = Column(String)
    routes = relationship("Route", back_populates="user")  # Связь с маршрутами


# Модель маршрута
class Route(Base):
    __tablename__ = 'routes'
    route_id = Column(Integer, primary_key=True, unique=True, nullable=False, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # ID пользователя, создавшего маршрут
    distance = Column(Float)  # Расстояние маршрута
    users_travel_time = Column(Integer)  # Время путешествия пользователя (в секундах)
    avg_travel_time_on_foot = Column(Integer)  # Среднее время путешествия пешком (считается со средней скоростью 6км/ч)
    avg_travel_velo_time = Column(Integer)  # Среднее время путешествия на велосипеде(считается со средней скоростью 16.3 км/ч)
    comment = Column(String)  # Комментарий к маршруту
    operation_time = Column(DateTime)  # Время создания маршрута
    user = relationship("User", back_populates="routes")  # Связь с пользователем
    estimations = relationship("Estimation", back_populates="route")  # Связь с оценками маршрута
    coordinates = relationship("Coordinate", back_populates="routes")  # Связь с координатами маршрута


# Модель координаты
class Coordinate(Base):
    __tablename__ = 'coordinates'
    cord_id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    route_id = Column(Integer, ForeignKey('routes.route_id'), nullable=False)  # ID маршрута
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # ID пользователя, добавившего координату
    latitude = Column(Float, nullable=False)  # Широта
    longitude = Column(Float, nullable=False)  # Долгота
    order = Column(Integer, nullable=True)  # Порядок координаты в маршруте
    locname = Column(String)  # Название местоположения
    operation_time = Column(DateTime, nullable=False)  # Время добавления координаты
    routes = relationship("Route", back_populates="coordinates")  # Связь с маршрутом


# Модель оценки маршрута
class Estimation(Base):
    __tablename__ = 'estimations'
    estimation_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    route_id = Column(Integer, ForeignKey('routes.route_id'), nullable=False)  # ID маршрута
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # ID пользователя, оставившего оценку
    estimation_value = Column(Integer, nullable=False)  # Значение оценки
    estimator_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # ID пользователя, оценившего маршрут
    datetime = Column(DateTime, nullable=False)  # Время оценки
    comment = Column(String)  # Комментарий к оценке
    route = relationship("Route", back_populates="estimations")  # Связь с маршрутом


# Создание всех таблиц в базе данных
Base.metadata.create_all(engine)
