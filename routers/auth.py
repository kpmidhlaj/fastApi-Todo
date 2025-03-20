from fastapi import HTTPException, Depends, status, APIRouter
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import datetime, timedelta
from jose import jwt, JWTError

from database import get_db

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15


class CreateUser(BaseModel):
    username: str
    email: Optional[str]
    first_name: str
    last_name: Optional[str]
    password: str
    phone_number: Optional[str]

    class Config:
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "bVz2l@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "password": "password123",
                "phone_number": "1234567890"
            }
        }


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")

router = APIRouter(prefix="/auth", tags=["auth"],
                   responses={401: {"user": "Not authenticated"}})


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


async def get_current_user(token: str = Depends(oauth2_bearer)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise get_user_exception()
        return {"username": username, "id": user_id}
    except JWTError:
        raise get_user_exception()


@router.post("/create_user", status_code=status.HTTP_201_CREATED)
async def create_new_user(user: CreateUser, db: Session = Depends(get_db)):
    from models import Users
    existing_user = db.query(Users).filter(
        or_(Users.email == user.email,
            Users.username == user.username)).first()
    if existing_user:
        raise already_exists()

    new_user = Users(
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=get_password_hash(user.password),
        is_active=True,
        phone_number=user.phone_number
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),
                                 db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise token_exception()
    token_expires = timedelta(minutes=20)
    token = create_access_token(user.username, user.id, expires_delta=token_expires)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/users/me", dependencies=[Depends(get_current_user)])
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return current_user


@router.get("/users")
async def get_all_users(db: Session = Depends(get_db)):
    from models import Users
    return db.query(Users).all()


# Error Handlers
def already_exists():
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                        detail="User already exists")


def get_user_exception():
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                         detail="Could not validate credentials",
                         headers={"WWW-Authenticate": "Bearer"})


def token_exception():
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                         detail="Incorrect username or password",
                         headers={"WWW-Authenticate": "Bearer"})
