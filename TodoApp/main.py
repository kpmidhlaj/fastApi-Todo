from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from TodoApp.database import engine
from TodoApp.routers import auth, todos
from TodoApp import models

app = FastAPI(title="Todo API", version="1.0.0",
              description="A FastAPI Todo application with authentication.")

models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(todos.router)


@app.get("/")
async def root():
    return {"message": "Welcome to the Todo API!"}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Todos API",
        version="1.0.0",
        description="API for managing todos",
        routes=app.routes
    )
    openapi_schema["components"]["securitySchemes"]["OAuth2PasswordBearer"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
