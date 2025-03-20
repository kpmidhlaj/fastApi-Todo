from typing import Optional
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from TodoApp.database import get_db
from TodoApp.models import Todo
from TodoApp.routers.auth import get_current_user, get_user_exception

router = APIRouter(prefix="/todos", tags=["todos"],
                   responses={401: {"description": "Not Found"}})


class TodoRequest(BaseModel):
    title: str = Field(min_length=1)
    description: Optional[str] = Field(min_length=1)
    priority: int = Field(gt=0, lt=6, description="Priority must be between 1 and 5")
    completed: bool

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Buy Groceries",
                "description": "Milk, Bread, and Eggs",
                "priority": 2,
                "completed": False
            }
        }


@router.get("/")
async def read_all(db: Session = Depends(get_db)):
    return db.query(Todo).all()


@router.get("/user")
async def read_all_by_user(user: dict = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()
    return db.query(Todo).filter(user.get("id") == Todo.owner_id).all()


@router.get("/{todo_id}")
async def read_todo(todo_id: int, user: dict = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()

    todo_model = db.query(Todo).filter(todo_id == Todo.id,
                                       Todo.owner_id == user.get("id")).first()
    if todo_model:
        return todo_model

    raise http_exception()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_todo(todo: TodoRequest, db: Session = Depends(get_db),
                      user: dict = Depends(get_current_user)):
    if user is None:
        raise get_user_exception()

    todo_model = Todo(**todo.model_dump(), owner_id=user.get("id"))
    db.add(todo_model)
    db.commit()
    db.refresh(todo_model)
    return successful_transaction(201)


@router.put("/{todo_id}")
async def update_todo(todo_id: int, todo: TodoRequest, db: Session = Depends(get_db),
                      user: dict = Depends(get_current_user)):
    if user is None:
        raise get_user_exception()

    todo_model = db.query(Todo).filter(todo_id == Todo.id,
                                       Todo.owner_id == user.get("id")).first()
    if todo_model:
        todo_model.title = todo.title
        todo_model.description = todo.description
        todo_model.priority = todo.priority
        todo_model.completed = todo.completed
        db.commit()
        return successful_transaction(200)

    raise http_exception()


@router.delete("/{todo_id}")
async def delete_todo(todo_id: int, db: Session = Depends(get_db),
                      user: dict = Depends(get_current_user)):
    if user is None:
        raise get_user_exception()

    todo_model = db.query(Todo).filter(todo_id == Todo.id,
                                       Todo.owner_id == user.get("id")).first()
    if todo_model:
        db.delete(todo_model)
        db.commit()
        return successful_transaction(200)

    raise http_exception()


def successful_transaction(status_code: int):
    return {"status": status_code, "transaction": "success"}


def http_exception():
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
