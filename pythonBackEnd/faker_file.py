from faker import Faker
from sqlalchemy import func

from PPgroup5.pythonBackEnd.auth.database import User, Route, Coordinate, Estimation, session
import random


fake = Faker()

# Для удаленных пользователей
if not session.query(User).filter(User.id == 0).first():
    session.add(User(
        id=0,
        name="Deleted users",
        email="0",
        telephone_number="0",
        hashed_password="0",
        salt_hashed_password="0",
        token_mobile="0"
    ))

session.add(User(
    name=fake.name(),
    hashed_password=fake.password(),
    telephone_number=str(random.randint(10 ** 10, 10 ** 11 - 1)),
    salt_hashed_password=fake.password(),
    token_mobile=random.randint(10000, 100000)
))
session.commit()
max_user_id = session.query(func.max(User.id)).scalar()
session.add(Route(
    user_id=max_user_id,
    distance=random.uniform(1, 100)
))
session.commit()
max_route_id = session.query(func.max(Route.route_id)).scalar()

for i in range(1, 50):
    user = User(
        name=fake.name(),
        hashed_password=fake.password(),
        telephone_number=str(random.randint(10**10, 10**11 - 1)),
        salt_hashed_password=fake.password(),
        token_mobile=random.randint(10000, 100000)
    )
    session.add(user)
    route = Route(
        user_id=random.randint(max_user_id, max_user_id + i),
        distance=random.uniform(1, 100)
    )
    session.add(route)
    estimation = Estimation(
        route_id=random.randint(max_route_id, max_route_id + i),
        estimation_value=random.randint(0, 5),
        user_id=random.randint(max_user_id, max_user_id + i),
        estimator_id=random.randint(max_user_id, max_user_id + i),
        datetime=fake.date_time()
    )
    session.add(estimation)
for u in range(1, 50):
    route_id = random.randint(max_route_id, max_route_id + 49)  # Генерация случайного route_id
    user_id = random.randint(max_user_id, max_user_id + 49)  # Генерация случайного user_id
    for y in range(5):
        coordinate = Coordinate(
            latitude=random.uniform(-90, 90),
            longitude=random.uniform(-180, 180),
            operation_time=fake.date_time(),
            route_id=route_id,
            user_id=user_id
        )
        session.add(coordinate)
session.commit()

