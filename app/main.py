from jose import jwt
from fastapi import Request
from fastapi import FastAPI, Depends
from jose.exceptions import JWTError
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.main import router as main_router
from app.api.users import router as user_router
from app.config.auth import SECRET_KEY, ALGORITHM
from app.services.user_service import UserService
from app.api.analysis import router as analysis_router
from app.services.cleanup_service import CleanupService
from app.domain.models.database import AsyncSessionLocal
from app.auth.auth import verify_token, create_access_token
from fastapi.responses import HTMLResponse, RedirectResponse
# Предзагружаем все модели для инициализации отношений
import app.domain.models

def create_app() -> FastAPI:
    app = FastAPI()

    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    templates = Jinja2Templates(directory="app/templates")

    # Инициализация сервиса очистки
    cleanup_service = CleanupService()

    @app.on_event("startup")
    async def startup_event():
        await cleanup_service.start()

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        return RedirectResponse(url="/")

    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        return templates.TemplateResponse("main.html", {"request": request})
    
    @app.get("/protected-route")
    async def protected_route(username: str = Depends(verify_token)):
        return {"message": f"Hello, {username}!"}
    
    @app.middleware("http")
    async def check_token(request: Request, call_next):
        if (request.url.path.startswith("/users/") and not request.cookies.get("access_token") and not request.cookies.get("refresh_token")) or request.url.path.startswith("/static/") or request.url.path == "/":
            return await call_next(request)
        if not request.cookies.get("access_token") and not request.cookies.get("refresh_token") and not request.url.path.startswith("/users/") and not request.url.path.startswith("/static/") and request.url.path != "/":
            return RedirectResponse(url="/users/")
        try:
            access_token = request.cookies.get("access_token")
            refresh_token = request.cookies.get("refresh_token")
            if not access_token and not refresh_token:
                return RedirectResponse(url="/users/")
            elif refresh_token and not access_token:
                async with AsyncSessionLocal() as db2:
                    user_service = UserService(db2)
                    user = await user_service.get_refresh_token(refresh_token=refresh_token)
                    if user is None:
                        response.cookies.delete("refresh_token")
                        return RedirectResponse(url="/users/")
                    access_token = create_access_token({"sub": jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM]).get("sub")})
                    response = await call_next(request)
                    response.set_cookie(
                        key="access_token",
                        value=access_token,
                        httponly=True,
                        samesite="Lax",
                        max_age=30*60
                    )
                    return response
            try:
                payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
                username = payload.get("sub")
                if not username:
                    return RedirectResponse(url="/users/")
            except JWTError as e:
                return RedirectResponse(url="/users/")
        except Exception as e:
            return RedirectResponse(url="/users/")
        response = await call_next(request)
        return response

    app.include_router(user_router)
    app.include_router(analysis_router)
    app.include_router(main_router)

    @app.on_event("shutdown")
    async def shutdown_event():
        await cleanup_service.stop()

    return app