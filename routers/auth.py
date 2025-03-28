from dns.dnssec import validate
from fastapi import HTTPException, Depends, status, APIRouter, Request, Response, Form
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse

import models
from database import get_db

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

templates = Jinja2Templates(directory="templates")

# class CreateUser(BaseModel):
#     username: str
#     email: Optional[str]
#     first_name: str
#     last_name: Optional[str]
#     password: str
#     phone_number: Optional[str]
#
#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "username": "johndoe",
#                 "email": "bVz2l@example.com",
#                 "first_name": "John",
#                 "last_name": "Doe",
#                 "password": "password123",
#                 "phone_number": "1234567890"
#             }
#         }


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")

router = APIRouter(prefix="/auth", tags=["auth"],
                   responses={401: {"user": "Not authenticated"}})


class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def create_oauth_form(self):
        form = await self.request.form()
        self.username = form.get('email')
        self.password = form.get('password')


def get_password_hash(password):
    return bcrypt_context.hash(password)


def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str, db: Session):
    from models import Users
    user = db.query(Users).filter(username == Users.username).first()
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(username: str, user_id: int,
                        expires_delta: Optional[timedelta] = None):
    encode = {"sub": username, "id": user_id}
    expire = datetime.now() + (expires_delta if expires_delta else timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    encode.update({"exp": expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(request: Request):
    try:
        token = request.cookies.get("access_token")
        if token is None:
            return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
        return {"username": username, "id": user_id}
    except JWTError:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)


# @router.post("/create_user", status_code=status.HTTP_201_CREATED)
# async def create_new_user(user: CreateUser, db: Session = Depends(get_db)):
#     from models import Users
#     existing_user = db.query(Users).filter(
#         or_(Users.email == user.email,
#             Users.username == user.username)).first()
#     if existing_user:
#         raise already_exists()
#
#     new_user = Users(
#         username=user.username,
#         email=user.email,
#         first_name=user.first_name,
#         last_name=user.last_name,
#         hashed_password=get_password_hash(user.password),
#         is_active=True,
#         phone_number=user.phone_number
#     )
#
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)
#     return new_user


@router.post("/token")
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db), ) -> bool:
    user = authenticate_user(
        username=form_data.username, password=form_data.password, db=db
    )
    if not user:
        # raise HTTPException(status_code=404, detail="User not found")
        return False  # raise token_exception()
    # return "User Validated"
    token_expires = timedelta(minutes=60)
    token = create_access_token(
        username=user.username, user_id=user.id, expires_delta=token_expires
    )
    response.set_cookie(key="access_token", value=token, httponly=True)  # mutates state
    return True  # {"token": token}


@router.get("/", response_class=HTMLResponse)
async def authentication_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/", response_class=HTMLResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    try:
        form = LoginForm(request=request)
        await form.create_oauth_form()
        response = RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)
        validate_user_cookie = await login_for_access_token(
            response=response, form_data=form, db=db
        )
        if not validate_user_cookie:
            msg = "Incorrect Username or Password"
            return templates.TemplateResponse(
                "login.html", {"request": request, "msg": msg}
            )
        return response
    except HTTPException:
        msg = "Unknown Error"
        return templates.TemplateResponse(
            "login.html", {"request": request, "msg": msg})


@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    msg = "Logout Successful"
    response = templates.TemplateResponse('login.html',
                                          {'request': request, 'msg': msg})
    response.delete_cookie("access_token")
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse('register.html', {'request': request})


@router.post("/register", response_class=HTMLResponse)
async def register_user(request: Request, email: str = Form(...),
                        username: str = Form(...), firstname: str = Form(...),
                        lastname: str = Form(...), password: str = Form(...),
                        password2: str = Form(...),
                        db: Session = Depends(get_db)):
    validation1 = db.query(models.Users).filter(
        username == models.Users.username).first()
    validation2 = db.query(models.Users).filter(email == models.Users.email).first()

    if password != password2 or validation1 is not None or validation2 is not None:
        msg = "Invalid registration request"
        return templates.TemplateResponse("register.html",
                                          {"request": request, "msg": msg})
    user_model = models.Users()
    user_model.username = username
    user_model.email = email
    user_model.first_name = firstname
    user_model.last_name = lastname
    hash_pass = get_password_hash(password)
    user_model.hashed_password = hash_pass
    user_model.is_active = True
    db.add(user_model)
    db.commit()

    msg = "User successfully created"
    return templates.TemplateResponse("login.html", {"request": request, "msg": msg})


@router.get("/users/me", dependencies=[Depends(get_current_user)])
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return current_user


@router.get("/users")
async def get_all_users(db: Session = Depends(get_db)):
    from models import Users
    return db.query(Users).all()


# Error Handlers
# def already_exists():
#     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
#                         detail="User already exists")


def get_user_exception():
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                         detail="Could not validate credentials",
                         headers={"WWW-Authenticate": "Bearer"})

# def token_exception():
#     return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                          detail="Incorrect username or password",
#                          headers={"WWW-Authenticate": "Bearer"})
