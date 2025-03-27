from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from database import engine
from routers import auth, todos, address
from routers import users
import models
from starlette.staticfiles import StaticFiles
from starlette import status
from starlette.responses import RedirectResponse

app = FastAPI(title="Todo API", version="1.0.0",
              description="A FastAPI Todo application with authentication.")

models.Base.metadata.create_all(bind=engine)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)


app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(address.router)
app.include_router(users.router)


@app.get("/check_server")
async def check_server():
    return {"message": "Server is running"}


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
