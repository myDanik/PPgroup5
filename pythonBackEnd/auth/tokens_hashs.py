import secrets
import string
import hashlib
import jwt
import os
from datetime import datetime, timedelta
from PPgroup5.pythonBackEnd.pg import SECRET_KEY
from PPgroup5.pythonBackEnd.database.database import User, session


def generate_token(length=10):
    alphabet = string.ascii_letters + string.digits
    token_mobile = ''.join(secrets.choice(alphabet) for _ in range(length))
    user = session.query(User).filter_by(token_mobile=token_mobile).first()
    if user is None:
        return token_mobile
    return generate_token()


def generate_salt():
    return os.urandom(16).hex()


def hash_password(password, salt):
    hash_input = f"{password}{salt}".encode('utf-8')
    hashed_password = hashlib.sha256(hash_input).hexdigest()
    return hashed_password


def creating_hash_salt(password):
    salt = generate_salt()
    hashed_password = hash_password(password, salt)
    return salt, hashed_password


def create_token(user_id: int, expires_delta: timedelta):
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + expires_delta
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Токен истек
    except jwt.InvalidTokenError:
        return None  # Неверный токен


def token_user(token):
    if token:
        if verify_token(token):
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = int(payload.get("sub"))
            return user_id
    return None


def authenticated_user(entry_password, hashed_password, salt):
    return hash_password(entry_password, salt) == hashed_password
