import sys

from sqlalchemy.orm import Session

from TodoApp import models
from TodoApp.routers.auth import get_current_user, get_user_exception, verify_password, \
    get_password_hash

sys.path.append("..")

from fastapi import Depends, APIRouter
from TodoApp.database import engine, get_db

from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["users"],
                   responses={404: {"description": "Not Found"}})

models.Base.metadata.create_all(bind=engine)


class UserVerification(BaseModel):
    username: str
    password: str
    new_password: str


@router.get("/")
async def read_all(db: Session = Depends(get_db)):
    return db.query(models.Users).all()


@router.get("/user/{user_id}")
async def read_user(user_id: int, db: Session = Depends(get_db)):
    user_model = db.query(models.Users).filter(user_id == models.Users.id).first()
    if user_model:
        return user_model
    return 'Invalid user id'


@router.get('/user')
async def read_user_by_query(user_id: int, db: Session = Depends(get_db)):
    user_model = db.query(models.Users).filter(user_id == models.Users.id).first()
    if user_model:
        return user_model
    return 'Invalid user id'


@router.put('/user/password')
async def update_password(user_verification: UserVerification,
                          db: Session = Depends(get_db),
                          user: dict = Depends(get_current_user)):
    if user is None:
        raise get_user_exception()

    user_model = db.query(models.Users).filter(
        user.get("id") == models.Users.id).first()
    if user_model is not None:
        if user_verification.username == user_model.username and verify_password(
            user_verification.password, user_model.hashed_password):
            user_model.hashed_password = get_password_hash(
                user_verification.new_password)
            db.add(user_model)
            db.commit()
            db.refresh(user_model)
            return "Password updated successfully"
    return "Invalid username or password"


@router.delete('/user')
async def delete_user(db: Session = Depends(get_db),
                      user: dict = Depends(get_current_user)):
    if user is None:
        raise get_user_exception()

    user_model = db.query(models.Users).filter(
        user.get("id") == models.Users.id).first()
    if user_model is not None:
        db.delete(user_model)
        db.commit()
        return "User deleted successfully"
    return "Invalid user id"
