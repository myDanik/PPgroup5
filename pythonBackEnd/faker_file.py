from faker import Faker
from PPgroup5.pythonBackEnd.auth.database import User, Route, Coordinate, Estimation, session
import random


fake = Faker()
# Для удаленных пользователей
session.add(User(
    id=0,
    name="Deleted users",
    login="0",
    hashed_password="0",
    salt_hashed_password="0",
    token_mobile="0"
))
for i in range(1, 51):
    user = User(name=fake.name(), login=fake.user_name(), hashed_password=fake.password(),
                salt_hashed_password=fake.password(), token_mobile=random.randint(10000, 100000))
    session.add(user)
    route = Route(user_id=random.randint(1, i), estimation=random.uniform(0, 5),
                  distance=random.uniform(1, 100))
    session.add(route)
    estimation = Estimation(
        route_id=random.randint(1, i), estimation_value=random.randint(0, 5),
        user_id=random.randint(1, i), estimator_id=random.randint(1, 50), datetime=fake.date_time()
    )
    session.add(estimation)
for u in range(1, 51):
    route_id = random.randint(1, 50)  # Генерация случайного route_id
    user_id = random.randint(1, 50)  # Генерация случайного user_id
    for y in range(1, 51):
        coordinate = Coordinate(latitude=random.uniform(-90, 90), longitude=random.uniform(-180, 180),
                                operation_time=fake.date_time(), route_id=route_id, user_id=user_id)
        session.add(coordinate)

session.commit()
