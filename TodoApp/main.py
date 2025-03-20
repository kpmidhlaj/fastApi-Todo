from typing import Optional

from fastapi import FastAPI, Depends, status, HTTPException
from fastapi.openapi.utils import get_openapi
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from TodoApp.database import engine, get_db

from TodoApp.routers.auth import get_current_user, get_user_exception

from TodoApp.routers import auth

from TodoApp import models

app = FastAPI()

models.Base.metadata.create_all(bind=engine)
app.include_router(auth.router)


class Todo(BaseModel):
    title: str = Field(min_length=1)
    description: Optional[str] = Field(min_length=1)
    priority: int = Field(gt=0, lt=6, description="Priority must be between 1 and 5")
    completed: bool

    class Config:
        json_schema_extra = dict(
            example=dict(title="title one", description="description one",
                         priority=1, completed=False))


@app.get("/")
async def read_all(db: Session = Depends(get_db)):
    return db.query(models.Todo).all()


@app.get("/todos/user")
async def read_all_by__user(user: dict = Depends(get_current_user),
                            db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()
    return db.query(models.Todo).filter(user.get("id") == models.Todo.owner_id).all()


@app.get("/todos/{todo_id}")
async def read_todo(todo_id: int, user: dict = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()
    todo_model = db.query(models.Todo).filter(todo_id == models.Todo.id).filter(
        models.Todo.owner_id == user.get("id")).first()
    if todo_model is not None:
        return todo_model
    raise http_exception()


@app.post("/", status_code=status.HTTP_201_CREATED)
async def create_todo(todo: Todo, db: Session = Depends(get_db),
                      user: dict = Depends(get_current_user)):
    if user is None:
        raise get_user_exception()
    todo_model = models.Todo(**todo.model_dump(), owner_id=user.get("id"))
    db.add(todo_model)
    db.commit()
    db.refresh(todo_model)
    return successful_transaction(201)


@app.put("/{todo_id}")
async def update_todo(todo_id: int, todo: Todo, db: Session = Depends(get_db),
                      user: dict = Depends(get_current_user)):
    if user is None:
        raise get_user_exception()
    todo_model = db.query(models.Todo).filter(todo_id == models.Todo.id).filter(
        models.Todo.owner_id == user.get("id")).first()
    if todo_model is not None:
        todo_model.title = todo.title
        todo_model.description = todo.description
        todo_model.priority = todo.priority
        todo_model.completed = todo.completed
        db.add(todo_model)
        db.commit()
        db.refresh(todo_model)
        return successful_transaction(200)
    raise http_exception()


@app.delete("/{todo_id}")
async def delete_todo(todo_id: int, db: Session = Depends(get_db),
                      user: dict = Depends(get_current_user)):
    if user is None:
        raise get_user_exception()
    todo_model = db.query(models.Todo).filter(todo_id == models.Todo.id).filter(
        models.Todo.owner_id == user.get("id")).first()
    if todo_model is not None:
        db.delete(todo_model)
        db.commit()
        return successful_transaction(200)
    raise http_exception()


def successful_transaction(status_code: int):
    return dict(status=status_code, transaction='success')


def http_exception():
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Todos API",
        version="1.0.0",
        description="API for managing todos",
        routes=app.routes)
    openapi_schema["components"]["securitySchemes"]["OAuth2PasswordBearer"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT"}
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
