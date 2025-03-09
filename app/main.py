from fastapi import FastAPI
from app.api.users import router as user_router
from app.api.analysis import router as main_router


def create_app() -> FastAPI:
    app = FastAPI()

    app.include_router(user_router)
    app.include_router(main_router)

    return app