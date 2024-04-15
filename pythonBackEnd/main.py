from fastapi import FastAPI, HTTPException, Depends
from PPgroup5.pythonBackEnd.auth.database import User
from PPgroup5.pythonBackEnd.auth.jwt import generate_token
from PPgroup5.pythonBackEnd.auth.models import UserDB
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(f'postgresql://postgres:postgres@localhost:5432/postgres')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session = sessionmaker(engine)

app = FastAPI(title='Veloapp')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users/")
def create_user(user_data: UserDB, db: Session = Depends(get_db)):
    token = generate_token()
    new_user = User(
        name=user_data.name,
        login=user_data.login,
        password=user_data.password,
        token=token
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message: "f"Success, {new_user.name}, welcome!", new_user}


@app.get("/users/{user_id}")
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"name": user.name, "id": user.id, "login": user.login, "token": user.token}


@app.put("/users/{user_id}")
def update_user(user_id: int, user_data: UserDB, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for attr, value in user_data.dict(exclude_unset=True).items():
        setattr(user, attr, value)
    db.commit()
    db.refresh(user)
    return {"message: "f"Success, user {user.name} was updated"}


@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.refresh(user)
    db.commit()
    return {"message: "f"Success, {user.name} with user id {user_id} was deleted"}
