from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from auth.database import Base, User, Route, Coordinate, Estimation
from datetime import datetime
from pg import url
import random

engine = create_engine(url)

Session = sessionmaker(bind=engine)
session = Session()

fake = Faker()

for i in range(50):
    user = User(id = i, name=fake.name(), login=fake.user_name(), hashed_password=fake.password(), salt_hashed_password=fake.password(), token_mobile=random.randint(10000,100000))
    session.add(user)
    route = Route(route_id=i, user_id=random.randint(0, 49), estimation=random.uniform(0, 5),
                  distance=random.uniform(1, 100))
    session.add(route)
    estimation = Estimation(route_id=random.randint(1, 10), estim=random.randint(0, 5), user_id=random.randint(1, 10),
                           estimator_id=random.randint(1, 10), datetime=fake.date_time())
    session.add(estimation)
for u in range(10):
    n = random.randint(0, 49)
    for y in range(50):
        coordinate = Coordinate(latitude=random.uniform(-90, 90), longitude=random.uniform(-180, 180),
                                operation_time=fake.date_time(), route_id=u, user_id=n)
        session.add(coordinate)

session.commit()
