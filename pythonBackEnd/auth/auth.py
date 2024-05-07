from datetime import timedelta
from fastapi import HTTPException, Depends, APIRouter

from PPgroup5.pythonBackEnd.auth.database import User, get_db, Session
from PPgroup5.pythonBackEnd.auth.models import UserLogin, UserSignUp
from PPgroup5.pythonBackEnd.auth.schemas import is_login, error_login_email_userexists, \
    error_login_telephone_userexists, error_login_udentified, nothing
from PPgroup5.pythonBackEnd.auth.tokens_hashs import verify_token, authenticated_user, create_token, token_user, \
    generate_token, creating_hash_salt

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
    session.refresh(user)
    entry_token = create_token(user.id, timedelta(hours=12))
    return {"status": "success",
            "data": {
                "entry_token": entry_token,
                "user": user
            },
            "details": None
            }


@router.post("/login")
def login(login_user: UserLogin, entry_token: str = None, db: Session = Depends(get_db)):
    if token_user(entry_token):
        user_id = token_user(entry_token)
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                return {"status": "success",
                        "data": {
                            "entry_token": entry_token,
                            "id": user.id,
                            "name": user.name,
                            "telephone_number": user.telephone_number,
                            "email": user.email,
                            "token_mobile": user.token_mobile
                        },
                        "details": None
                        }
            raise HTTPException(status_code=404, detail={
                "status": "error",
                "data": None,
                "details": "Invalid token"
            })
    telephone_number, email, user = is_login(login_user.login, nothing, nothing, error_login_udentified)
    if user:
        if authenticated_user(login_user.password, user.hashed_password, user.salt_hashed_password):
            entry_token = create_token(user.id, timedelta(hours=2))
            return {"status": "success",
                    "data": {
                        "entry_token": entry_token,
                        "user": user
                    },
                    "details": None
                    }
    raise HTTPException(status_code=404, detail={
        "status": "error",
        "data": None,
        "details": "Incorrect login or password"
    })


@router.post("/logout")
def logout(token: str):
    if verify_token(token):
        return {"status": "success",
                "data": {
                    "entry_token": None,
                },
                "details": "Token was verified"
                }
    return {"status": "success",
            "data": {
                "entry_token": None,
            },
            "details": "Token was not verified"
            }
