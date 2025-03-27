from typing import Optional
from fastapi import APIRouter, Depends, status, HTTPException, Request, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from starlette.responses import RedirectResponse
from starlette import status

from database import get_db

from models import Todo
from routers.auth import get_current_user, get_user_exception
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/todos", tags=["todos"],
                   responses={401: {"description": "Not Found"}})
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def read_all_by_user(request: Request, db: Session = Depends(get_db)):
    user = await  get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todos = db.query(Todo).filter(Todo.owner_id == user.get("id")).all()
    return templates.TemplateResponse("home.html", {"request": request, "todos": todos,"user":user})


@router.get('/add-todo', response_class=HTMLResponse)
async def add_new_todo(request: Request, db: Session = Depends(get_db)):
    user = await  get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("add-todo.html", {"request": request})


@router.post('/add-todo', response_class=HTMLResponse)
async def add_new_todo(request: Request, title: str = Form(...),
                       description: str = Form(...), priority: int = Form(...),
                       db: Session = Depends(get_db)):
    user = await  get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todo_model = Todo()
    todo_model.title = title
    todo_model.description = description
    todo_model.priority = priority
    todo_model.completed = False
    todo_model.owner_id = user.get('id')
    db.add(todo_model)
    db.commit()
    db.refresh(todo_model)
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)


@router.get('/edit-todo/{todo_id}', response_class=HTMLResponse)
async def edit_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
    user = await  get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todo_model = db.query(Todo).filter(todo_id == Todo.id).first()
    return templates.TemplateResponse("edit-todo.html",
                                      {"request": request, "todo": todo_model})


@router.post('/edit-todo/{todo_id}', response_class=HTMLResponse)
async def edit_todo(request: Request, todo_id: int, title: str = Form(...),
                    description: str = Form(...), priority: int = Form(...),
                    db: Session = Depends(get_db)):
    user = await  get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todo_model = db.query(Todo).filter(todo_id == Todo.id).first()
    todo_model.title = title
    todo_model.description = description
    todo_model.priority = priority
    db.commit()
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)


@router.get('/delete/{todo_id}', response_class=HTMLResponse)
async def delete_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
    user = await  get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todo_model = db.query(Todo).filter(todo_id == Todo.id).filter(
        user.get("id") == Todo.owner_id).first()
    if todo_model is None:
        return RedirectResponse(url='/todos', status_code=status.HTTP_302_FOUND)
    db.delete(todo_model)
    db.commit()
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)


@router.get('/complete/{todo_id}', response_class=HTMLResponse)
async def complete_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
    user = await  get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todo_model = db.query(Todo).filter(todo_id == Todo.id).first()
    todo_model.completed = not todo_model.completed
    db.add(todo_model)
    db.commit()
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

# class TodoRequest(BaseModel):
#     title: str = Field(min_length=1)
#     description: Optional[str] = Field(min_length=1)
#     priority: int = Field(gt=0, lt=6, description="Priority must be between 1 and 5")
#     completed: bool
#
#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "title": "Buy Groceries",
#                 "description": "Milk, Bread, and Eggs",
#                 "priority": 2,
#                 "completed": False
#             }
#         }
#
#
# @router.get("/test")
# async def test(request: Request):
#     return templates.TemplateResponse("login.html", {"request": request})
#
#
# @router.get("/")
# async def read_all(db: Session = Depends(get_db)):
#     return db.query(Todo).all()
#
#
# @router.get("/user")
# async def read_all_by_user(user: dict = Depends(get_current_user),
#                            db: Session = Depends(get_db)):
#     if user is None:
#         raise get_user_exception()
#     return db.query(Todo).filter(user.get("id") == Todo.owner_id).all()
#
#
# @router.get("/{todo_id}")
# async def read_todo(todo_id: int, user: dict = Depends(get_current_user),
#                     db: Session = Depends(get_db)):
#     if user is None:
#         raise get_user_exception()
#
#     todo_model = db.query(Todo).filter(todo_id == Todo.id,
#                                        Todo.owner_id == user.get("id")).first()
#     if todo_model:
#         return todo_model
#
#     raise http_exception()
#
#
# @router.post("/", status_code=status.HTTP_201_CREATED)
# async def create_todo(todo: TodoRequest, db: Session = Depends(get_db),
#                       user: dict = Depends(get_current_user)):
#     if user is None:
#         raise get_user_exception()
#
#     todo_model = Todo(**todo.model_dump(), owner_id=user.get("id"))
#     db.add(todo_model)
#     db.commit()
#     db.refresh(todo_model)
#     return successful_transaction(201)
#
#
# @router.put("/{todo_id}")
# async def update_todo(todo_id: int, todo: TodoRequest, db: Session = Depends(get_db),
#                       user: dict = Depends(get_current_user)):
#     if user is None:
#         raise get_user_exception()
#
#     todo_model = db.query(Todo).filter(todo_id == Todo.id,
#                                        Todo.owner_id == user.get("id")).first()
#     if todo_model:
#         todo_model.title = todo.title
#         todo_model.description = todo.description
#         todo_model.priority = todo.priority
#         todo_model.completed = todo.completed
#         db.commit()
#         return successful_transaction(200)
#
#     raise http_exception()
#
#
# @router.delete("/{todo_id}")
# async def delete_todo(todo_id: int, db: Session = Depends(get_db),
#                       user: dict = Depends(get_current_user)):
#     if user is None:
#         raise get_user_exception()
#
#     todo_model = db.query(Todo).filter(todo_id == Todo.id,
#                                        Todo.owner_id == user.get("id")).first()
#     if todo_model:
#         db.delete(todo_model)
#         db.commit()
#         return successful_transaction(200)
#
#     raise http_exception()
#
#
# def successful_transaction(status_code: int):
#     return {"status": status_code, "transaction": "success"}
#
#
# def http_exception():
#     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
