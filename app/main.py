from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi import Request, HTTPException, Response
from app.config.auth import SECRET_KEY, ALGORITHM
from jose import jwt
from jose.exceptions import JWTError
from app.api.users import router as user_router
from app.api.analysis import router as analysis_router
from app.api.main import router as main_router
from app.auth.auth import verify_token, create_access_token
from datetime import timedelta
from app.services.user_service import UserService
from app.domain.models.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.auth import refresh_token as rt
from app.domain.models.database import AsyncSessionLocal

def create_app() -> FastAPI:
    app = FastAPI()

    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        # Перенаправление на главную страницу или другую страницу
        return RedirectResponse(url="/")

    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        return RedirectResponse(url="/analysis")
    
    @app.get("/protected-route")
    async def protected_route(username: str = Depends(verify_token)):
        return {"message": f"Hello, {username}!"}
    
    @app.middleware("http")
    async def check_token(request: Request, call_next):
        if request.url.path.startswith("/users/") or request.url.path.startswith("/static/") or request.url.path == "/":
            return await call_next(request)
        try:
            access_token = request.cookies.get("access_token")
            print(access_token, "access")
            refresh_token = request.cookies.get("refresh_token")
            if not access_token and not refresh_token:
                print("Нет токенов")
                return RedirectResponse(url="/users/")
            elif refresh_token and not access_token:
                print("Да, попал")
                async with AsyncSessionLocal() as db2:
                    user_service = UserService(db2)
                    user = await user_service.get_refresh_token(refresh_token=refresh_token)
                    if user is None:
                        return RedirectResponse(url="/users/")
                    access_token = create_access_token({"sub": jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM]).get("sub")})
                    response = await call_next(request)
                    response.set_cookie(
                        key="access_token",
                        value=access_token,
                        httponly=True,
                        samesite="Lax",
                        # secure=True,
                        max_age=30*60
                    )
                    return response
            try:
                payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
                print(payload)
                username = payload.get("sub")
                if not username:
                    print("username")
                    return RedirectResponse(url="/users/")
            except JWTError as e:
                print("JWTError", e)
                return RedirectResponse(url="/users/")
        except Exception as e:
            print(e)
            return RedirectResponse(url="/users/")
        response = await call_next(request)
        return response

    app.include_router(user_router)
    app.include_router(analysis_router)
    app.include_router(main_router)

    return app