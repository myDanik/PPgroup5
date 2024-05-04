from datetime import timedelta

from fastapi import HTTPException, Depends, APIRouter

from PPgroup5.pythonBackEnd.auth.database import User, get_db, Session
from PPgroup5.pythonBackEnd.auth.models import UserLogin, UserDB
from PPgroup5.pythonBackEnd.auth.tokens_hashs import verify_token, authenticate_user, create_token, token_user, \
    generate_token, creating_hash_salt


router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


@router.post("/authorization")
def create_user(user_data: UserDB, db: Session = Depends(get_db)):
    if db.query(User).filter(User.login == user_data.login).first():
        raise HTTPException(status_code=409, detail={
            "status": "error",
            "data": None,
            "details": "Login is already exists"
        })
    generated_salt, hashed_password = creating_hash_salt(user_data.password)
    new_user = User(
        name=user_data.name,
        login=user_data.login,
        hashed_password=hashed_password,
        token_mobile=generate_token(),
        salt_hashed_password=generated_salt
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    entry_token = create_token(new_user.id, timedelta(hours=12))
    return {"status": "success",
            "data": {
                "entry_token": entry_token,
                "id": new_user.id,
                "name": new_user.name,
                "login": new_user.login,
                "token_mobile": new_user.token_mobile
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
                            "login": user.login,
                            "token_mobile": user.token_mobile
                        },
                        "details": None
                        }
            raise HTTPException(status_code=404, detail={
                "status": "error",
                "data": None,
                "details": "Invalid token"
            })
    user = db.query(User).filter(User.login == login_user.login).first()
    if user:
        if authenticate_user(login_user.password, user.hashed_password, user.salt_hashed_password):
            entry_token = create_token(user.id, timedelta(hours=2))
            return {"status": "success",
                    "data": {
                        "entry_token": entry_token,
                        "id": user.id,
                        "name": user.name,
                        "login": user.login,
                        "token_mobile": user.token_mobile
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
