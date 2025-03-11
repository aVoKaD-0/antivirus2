from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Request
from app.api.users import router as user_router
from app.api.analysis import router as analysis_router
from app.api.main import router as main_router
from app.auth.auth import verify_token

def create_app() -> FastAPI:
    app = FastAPI()

    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        # Перенаправление на главную страницу или другую страницу
        return RedirectResponse(url="/")

    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        return RedirectResponse(url="/main")
    
    @app.get("/protected-route")
    async def protected_route(username: str = Depends(verify_token)):
        return {"message": f"Hello, {username}!"}

    app.include_router(user_router)
    app.include_router(analysis_router)
    app.include_router(main_router)

    return app