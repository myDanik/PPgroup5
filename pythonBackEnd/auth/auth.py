from fastapi import HTTPException, Depends, APIRouter

from PPgroup5.pythonBackEnd.database.database import User, get_db, Session
from PPgroup5.pythonBackEnd.auth.models import UserLogin, UserSignUp
from PPgroup5.pythonBackEnd.auth.schemas import is_login, error_login_email_userexists, \
    error_login_telephone_userexists, error_login_udentified, nothing
from PPgroup5.pythonBackEnd.auth.tokens_hashs import authenticated_user, generate_token, creating_hash_salt
from PPgroup5.pythonBackEnd.models.models import MyUserOut

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


@router.post("/authorization")
def create_user(user_data: UserSignUp, session: Session = Depends(get_db)):
    telephone_number, email, _ = is_login(user_data.login, error_login_telephone_userexists,
                                          error_login_email_userexists, error_login_udentified)
    generated_salt, hashed_password = creating_hash_salt(user_data.password)
    user = User(
        name=user_data.name,
        telephone_number=telephone_number,
        email=email,
        hashed_password=hashed_password,
        token_mobile=generate_token(),
        salt_hashed_password=generated_salt
    )
    session.add(user)
    session.commit()
    return {"status": "success",
            "data": {
                "user": MyUserOut(
                    id=user.id,
                    name=user.name,
                    email=user.email,
                    telephone_number=user.telephone_number,
                    surname=user.surname,
                    patronymic=user.patronymic,
                    location=user.location,
                    sex=user.sex,
                    token_mobile=user.token_mobile,
                    favorite_routes=user.favorite_routes
                )
            },
            "details": None
            }


@router.post("/login")
def login(login_user: UserLogin, session: Session = Depends(get_db)):
    telephone_number, email, user = is_login(login_user.login, nothing, nothing, error_login_udentified)
    if user:
        if authenticated_user(login_user.password, user.hashed_password, user.salt_hashed_password):
            return {"status": "success",
                    "data": {
                        "user": MyUserOut(
                            id=user.id,
                            name=user.name,
                            email=user.email,
                            telephone_number=user.telephone_number,
                            surname=user.surname,
                            patronymic=user.patronymic,
                            location=user.location,
                            sex=user.sex,
                            token_mobile=user.token_mobile,
                            favorite_routes=user.favorite_routes
                        )
                    },
                    "details": None
                    }

    raise HTTPException(status_code=404, detail={
        "status": "error",
        "data": None,
        "details": "Incorrect login or password"
    })