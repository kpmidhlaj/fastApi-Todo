import sys

sys.path.append("..")
from fastapi import APIRouter, Depends
from typing import Optional
import models
from database import get_db
from sqlalchemy.orm import Session
from pydantic import BaseModel
from .auth import get_current_user, get_user_exception

router = APIRouter(prefix="/address", tags=["address"],
                   responses={404: {"description": "Not Found"}})


class Address(BaseModel):
    address1: str
    address2: Optional[str]
    city: str
    state: str
    country: str
    postalcode: str
    apt_num: Optional[int]

    class Config:
        json_schema_extra = {
            "example": {
                "address1": "123 Main St",
                "address2": "Apt 4",
                "city": "New York",
                "state": "NY",
                "country": "USA",
                "postalcode": "10001",
                "apt_num": 4
            }
        }


@router.post("/")
async def create_address(address: Address, user: dict = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()
    address_model = models.Address(**address.model_dump())
    db.add(address_model)
    db.flush()
    user_model = db.query(models.Users).filter(
        user.get("id") == models.Users.id).first()
    user_model.address_id = address_model.id
    db.add(user_model)
    db.commit()
    db.refresh(address_model)
    return 'Address created successfully'
