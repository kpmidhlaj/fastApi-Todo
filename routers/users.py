import sys
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

import models
from routers.auth import get_current_user, get_user_exception, verify_password, \
    get_password_hash

sys.path.append("..")
from fastapi import Depends, APIRouter, Request, status, Form
from database import engine, get_db
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/users", tags=["users"],
                   responses={404: {"description": "Not Found"}})

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")


class UserVerification(BaseModel):
    username: str
    password: str
    new_password: str


@router.get('/edit-password', response_class=HTMLResponse)
async def edit_password(request: Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("edit-user-password.html",
                                      {"request": request, "user": user})


@router.post('/edit-password', response_class=HTMLResponse)
async def edit_password(request: Request, username: str = Form(...),
                        password: str = Form(...), password2: str = Form(...),
                        db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    user_data = db.query(models.Users).filter(username == models.Users.username).first()

    msg = "Invalid username or password"
    if user_data is not None:
        if user_data.username == username and verify_password(password,
                                                              user_data.hashed_password):
            user_data.hashed_password = get_password_hash(password2)
            db.add(user_data)
            db.commit()
            msg = "Password updated"

    return templates.TemplateResponse("edit-user-password.html",
                                      {"request": request, "msg": msg, "user": user})

# @router.get("/")
# async def read_all(db: Session = Depends(get_db)):
#     return db.query(models.Users).all()
#
#
# @router.get("/user/{user_id}")
# async def read_user(user_id: int, db: Session = Depends(get_db)):
#     user_model = db.query(models.Users).filter(user_id == models.Users.id).first()
#     if user_model:
#         return user_model
#     return 'Invalid user id'
#
#
# @router.get('/user')
# async def read_user_by_query(user_id: int, db: Session = Depends(get_db)):
#     user_model = db.query(models.Users).filter(user_id == models.Users.id).first()
#     if user_model:
#         return user_model
#     return 'Invalid user id'
#
#
# @router.put('/user/password')
# async def update_password(user_verification: UserVerification,
#                           db: Session = Depends(get_db),
#                           user: dict = Depends(get_current_user)):
#     if user is None:
#         raise get_user_exception()
#
#     user_model = db.query(models.Users).filter(
#         user.get("id") == models.Users.id).first()
#     if user_model is not None:
#         if user_verification.username == user_model.username and verify_password(
#             user_verification.password, user_model.hashed_password):
#             user_model.hashed_password = get_password_hash(
#                 user_verification.new_password)
#             db.add(user_model)
#             db.commit()
#             db.refresh(user_model)
#             return "Password updated successfully"
#     return "Invalid username or password"
#
#
# @router.delete('/user')
# async def delete_user(db: Session = Depends(get_db),
#                       user: dict = Depends(get_current_user)):
#     if user is None:
#         raise get_user_exception()
#
#     user_model = db.query(models.Users).filter(
#         user.get("id") == models.Users.id).first()
#     if user_model is not None:
#         db.delete(user_model)
#         db.commit()
#         return "User deleted successfully"
#     return "Invalid user id"
