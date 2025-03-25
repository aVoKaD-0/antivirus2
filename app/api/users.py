import pyotp
from fastapi import Response
from app.auth.auth import generate_code
from fastapi.staticfiles import StaticFiles
from app.domain.models.database import get_db
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer
from app.services.user_service import UserService
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi import APIRouter, HTTPException, Depends, Request
from app.auth.auth import verify_password, send_email, create_access_token, create_refresh_token
from app.schemas.user import SingUpRequest, SignInRequest, EmailConfirmation, ResetPasswordRequest


router = APIRouter(prefix="/users", tags=["users"])

router.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("user.html", {"request": request})

@router.post("/register")
async def register(response: Response, user: SingUpRequest, db: AsyncSession = Depends(get_db)):
    userservice = UserService(db)
    email = user.email.lower()
    mail = await userservice.get_user_by_email(email)
    if mail:
        raise HTTPException(status_code=400, detail="Email already registered")
    _, confirmation_code = await userservice.create_user(email, user.password)
    response.set_cookie(key="email", value=email, max_age=600)
    await send_email(email, f"Confirmation code: {confirmation_code}")
    return {"redirect_url": "/confirm-email"}

@router.get("/confirm-email", response_class=HTMLResponse)
def confirm_email_page(request: Request):
    if not request.cookies.get("email") or request.cookies.get("refresh_token") or request.cookies.get("access_token"):
        return RedirectResponse(url="/users/")
    return templates.TemplateResponse("confirm_email.html", {"request": request})

@router.post("/confirm")
async def confirm_email(request: Request, response: Response, EmailConfirmation: EmailConfirmation, db: AsyncSession = Depends(get_db)):
    userservice = UserService(db)
    email = request.cookies.get("email")
    user = await userservice.get_user_by_email(email)
    if user and EmailConfirmation.code == user.confiration_code:
        user.confirmed = True
        user.confiration_code = None
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        await userservice.update_refresh_token(email, refresh_token)
        response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=30*60)
        response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, max_age=7*24*60*60)
        await userservice.__commit__()
        return {"message": "Email confirmed"}
    raise HTTPException(status_code=400, detail="Invalid code")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/login")
async def login(User: SignInRequest, response: Response, db: AsyncSession = Depends(get_db)):
    userservice = UserService(db)
    email = User.email.lower()
    user = await userservice.get_user_by_email(email)
    if not user or not verify_password(User.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    await userservice.update_refresh_token(email, refresh_token)
    response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=30*60)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, max_age=7*24*60*60)

    return {"access_token": access_token, "refresh_token": refresh_token}

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

@router.get("/captcha")
async def generate_captcha():
    return generate_captcha

@router.post("/logout")
async def logout(response: Response, request: Request, db: AsyncSession = Depends(get_db)):
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")
    if (access_token and refresh_token) or (refresh_token and not access_token):
        user_service = UserService(db)
        user = await user_service.get_refresh_token(refresh_token=refresh_token)
        if user is None:
            return {"message": "Logout successful"}
        await user_service.update_refresh_token(user.email, None)
        print(user)
        if access_token:
            response.delete_cookie(key="access_token", httponly=True)
        response.delete_cookie(key="refresh_token", httponly=True)
    else:
        return RedirectResponse(url="/users/")
    return {"message": "Logout successful"}

@router.post("/resend-code")
async def reset_code_page(request: Request, db: AsyncSession = Depends(get_db)):
    email = request.cookies.get("email")
    if not email:
        return RedirectResponse(url="/users/")
    userservice = UserService(db)
    user = await userservice.get_user_by_email(email)
    confirmation_code = generate_code()
    user.confiration_code = confirmation_code
    await userservice.__commit__()
    await send_email(email, f"Confirmation code: {confirmation_code}")
    return JSONResponse(content={"message": "Email sent"})

@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        userservice = UserService(db)
        user = await userservice.get_refresh_token(refresh_token=refresh_token)
        if user is None:
            response.cookies.delete("refresh_token")
            return RedirectResponse(url="/users/")
    has_token = refresh_token is not None
    return templates.TemplateResponse(
        "reset_password.html", 
        {"request": request, "has_token": has_token}
    )

@router.post("/reset-password")
async def reset_password(request: Request, User: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    userservice = UserService(db)
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        user = await userservice.update_password(refresh_token=refresh_token, password=User.password)
        if user is None:
            if User.email:
                await userservice.update_password(User.email, User.password)
                return {"message": "Password updated successfully"}
            elif refresh_token:
                await userservice.update_password(refresh_token=refresh_token, password=User.password)
                return {"message": "Password updated successfully"}
            else:
                raise HTTPException(status_code=404, detail="User not found")
    else:
        if not User.email:
            raise HTTPException(status_code=400, detail="Email is required when not authenticated")
        await userservice.update_password(User.email, User.password)
    return {"message": "Password updated successfully"}