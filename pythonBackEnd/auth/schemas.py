import re
from fastapi import HTTPException
from geopy import Nominatim

from PPgroup5.pythonBackEnd.database.database import session, User


def is_telephone_number(telephone: str):
    if len(telephone) != 11:
        if not (len(telephone) == 12 and telephone.startswith("+")):
            return {"result": False,
                    "telephone": telephone,
                    "details": "length of telephone number"}
        telephone = telephone[1:]
    if not telephone.isdigit():
        return {"result": False,
                "telephone": telephone,
                "details": "telephone number not from digits"}
    return {"result": True,
            "telephone": telephone,
            "details": None}


def error_login_telephone_userexists():
    raise HTTPException(status_code=409, detail={
        "status": "error",
        "data": None,
        "details": "such telephone is already exists"
    })


def error_login_email_userexists():
    raise HTTPException(status_code=409, detail={
        "status": "error",
        "data": None,
        "details": "such email is already exists"
    })


def unidentified_login():
    raise HTTPException(status_code=409, detail={
        "status": "error",
        "data": None,
        "details": "unidentified login"
    })


def error_login_udentified():
    raise HTTPException(status_code=409, detail={
        "status": "error",
        "data": None,
        "details": "unidentified login"
    })


def nothing():
    pass


def is_valid_email(email):
    pattern = r"\"?([-a-zA-Z0-9.`?{}]+@\w+\.\w+)\"?"
    if not re.match(pattern, email):
        return False
    return True


def is_login(login, func_login_telephone=nothing(), func_login_email=nothing(), func_login_udentified=nothing()):
    if is_telephone_number(login)["result"]:
        user = session.query(User).filter(User.telephone_number == login).first()
        if user:
            func_login_telephone()
        telephone_number = is_telephone_number(login)["telephone"]
        email = None
    else:
        if is_valid_email(login):
            user = session.query(User).filter(User.email == login).first()
            if user:
                func_login_email()
            telephone_number = None
            email = login
        else:
            func_login_udentified()
    return telephone_number, email, user


def get_lock_by_cords(latitude, longitude):
    try:
        geoLoc = Nominatim(user_agent="GetLoc")
        locname = geoLoc.reverse(f"{str(latitude)}, {str(longitude)}")
        return locname
    except:
        return None
