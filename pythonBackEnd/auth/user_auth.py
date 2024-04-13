from fastapi import FastAPI, HTTPException
from PPgroup5.pythonBackEnd.auth.database import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/postgres'
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title='authetication')

@app.post("/users/")
def create_user(name, login, password, token):
    try:
        db = SessionLocal()
        new_user = User(name=name, login=login, password=password, token=token)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

