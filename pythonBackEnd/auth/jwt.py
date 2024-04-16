import secrets
import string

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from auth.database import User,engine


Session = sessionmaker(bind=engine)
session = Session()


def generate_token(length=10):
    alphabet = string.ascii_letters + string.digits
    token = ''.join(secrets.choice(alphabet) for _ in range(length))
    user = session.query(User).filter_by(token=token).first()
    if user is None:
        return token
    return generate_token()



# import hashlib
# import jwt
# from datetime import datetime, timedelta
#
# def generate_salt():
#     return os.urandom(16).hex()
#
# # Хеширование пароля
# def hash_password(password, salt):
#     hash_input = f"{password}{salt}".encode('utf-8')
#     hashed_password = hashlib.sha256(hash_input).hexdigest()
#     return hashed_password
#
# # Параметры
# password = "secret"
# salt = generate_salt()
#
# # Хеширование пароля с солью
# hashed_password = hash_password(password, salt)
#
# # Создание JWT с хешем пароля и солью в полезной нагрузке
# jwt_payload = {
#     "hashed_password": hashed_password,
#     "salt": salt
# }
#
# # Создание JWT
# jwt_token = jwt.encode(jwt_payload, 'secret_key', algorithm='HS256')
# print(jwt_token)
#
# # Секретный ключ для подписи токенов
# SECRET_KEY = "mysecretkey"
#
# # Создание токена
# def create_token(user_id: int, expires_delta: timedelta):
#     # Добавление дополнительных данных в токен (например, идентификатор пользователя)
#     payload = {
#         "sub": str(user_id),
#         "exp": datetime.utcnow() + expires_delta
#     }
#     token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
#     return token
#
# # Проверка токена
# def verify_token(token: str):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
#         return payload
#     except jwt.ExpiredSignatureError:
#         return None  # Токен истек
#     except jwt.InvalidTokenError:
#         return None  # Неверный токен
