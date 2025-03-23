from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List
from fastapi import Response
from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_service import UserService
# # from repositories.user_repository import UserRepository
from app.schemas.user import SingUpRequest, SignInRequest, EmailConfirmation
from app.domain.models.database import get_db
# from app.domain.models.user import Users
from app.auth.auth import generate_code, verify_password, send_email, create_access_token, create_refresh_token
from app.config.auth import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi_mail.errors import ConnectionErrors
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from jose import jwt, JWTError
import pyotp
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import JSONResponse
from fastapi.responses import RedirectResponse
from fastapi import status


router = APIRouter(prefix="/users", tags=["users"])

router.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("user.html", {"request": request})

@router.post("/register")
async def register(response: Response, user: SingUpRequest, db: AsyncSession = Depends(get_db)):
    userservice = UserService(db)
    mail = await userservice.get_user_by_email(user.email)
    if mail:
        raise HTTPException(status_code=400, detail="Email already registered")

    _, confirmation_code = await userservice.create_user(user.email, user.password)

    response.set_cookie(key="email", value=user.email, httponly=True, max_age=600)
    
    await send_email(user.email, f"Confirmation code: {confirmation_code}")

    return {"redirect_url": "/confirm-email"}

@router.get("/confirm-email", response_class=HTMLResponse)
def confirm_email_page(request: Request):
    return templates.TemplateResponse("confirm_email.html", {"request": request})

# === Подтверждение почты ===
@router.post("/confirm")
async def confirm_email(request: Request, EmailConfirmation: EmailConfirmation, db: AsyncSession = Depends(get_db)):
    userservice = UserService(db)
    email = request.cookies.get("email")
    user = await userservice.get_user_by_email(email)
    if user and EmailConfirmation.code == user.confiration_code:
        user.confirmed = True
        await userservice.__commit__()
        return {"message": "Email confirmed"}
    raise HTTPException(status_code=400, detail="Invalid code")

# === Логин ===
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/login")
async def login(User: SignInRequest, response: Response, db: AsyncSession = Depends(get_db)):
    userservice = UserService(db)
    user = await userservice.get_user_by_email(User.email)
    print(user)
    if not user or not verify_password(User.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    # user.refresh_token, uuid = refresh_token
    await userservice.update_refresh_token(User.email, refresh_token)
    response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=30*60)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, max_age=7*24*60*60)

    return {"access_token": access_token, "refresh_token": refresh_token}

# === Обновление токена ===
# @router.post("/refresh")
# async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
#     userservice = UserService(db)
#     try:
#         _, email = userservice.refresh_token(refresh_token)
#         user = userservice.get_user_by_email(email)
#         if not user or user.refresh_token != refresh_token:
#             raise HTTPException(status_code=401, detail="Invalid token")
#         new_access_token = user.create_token({"sub": user.id})
#         return {"access_token": new_access_token}
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid token")

# @router.post("/token")
# async def login(form_data: OAuth2PasswordRequestForm = Depends()):
#     user = users.get(form_data.username)
#     if not user or not verify_password(form_data.password, user["password"]):
#         raise HTTPException(status_code=400, detail="Invalid credentials")
    
#     if not user["confirmed"]:
#         raise HTTPException(status_code=400, detail="Email not confirmed")
    
#     access_token = create_token({"sub": form_data.username}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
#     refresh_token = create_token({"sub": form_data.username}, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
#     active_tokens[form_data.username] = refresh_token
    
#     return {
#         "access_token": access_token,
#         "refresh_token": refresh_token,
#         "token_type": "bearer"
#     }

# === 2FA ===
@router.post("/2fa")
async def two_factor_auth(email: str, db: AsyncSession = Depends(get_db)):
    userservice = UserService(db)
    user = userservice.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    totp = pyotp.TOTP(pyotp.random_base32())
    code = totp.now()
    
    send_email(email, f"Your 2FA code: {code}")

    userservice.__commit__()

    user.otp_code = code

    return {"message": "2FA code sent to email"}

@router.post("/validate-2fa")
async def validate_2fa(email: str, code: str, db: AsyncSession = Depends(get_db)):
    userservice = UserService(db)
    user = userservice.get_user_by_email(email)
    if user and user.get('2fa_code') == code:
        return {"message": "2FA success"}
    raise HTTPException(status_code=400, detail="Invalid 2FA code")

# === Капча ===
@router.get("/captcha")
async def generate_captcha():
    return generate_captcha

# # === Проксификация и защита через Cloudflare ===
# @router.middleware("http")
# async def block_bad_requests(request: Request, call_next):
#     # Защита от брутфорса или флуда
#     if "x-forwarded-for" not in request.headers:
#         return JSONResponse(status_code=403, content={"detail": "Blocked by proxy"})
#     response = await call_next(request)
#     return response

# # === Разрешенные хосты ===
# router.add_middleware(
#     TrustedHostMiddleware,
#     allowed_hosts=["your-domain.com", "*.your-domain.com"]
# )

# # === Защищенный эндпоинт ===
# @router.get("/protected")
# async def protected(token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username = payload.get("sub")
#         return {"message": f"Hello, {username}!"}
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid token")