import pyotp
from fastapi import Response
from fastapi.staticfiles import StaticFiles
from app.core.security import verify_password
from app.domain.models.database import get_db
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_password_hash
from fastapi.security import OAuth2PasswordBearer
from app.services.user_service import UserService
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from app.auth.auth import send_email, create_access_token, create_refresh_token, generate_code
from app.schemas.user import SingUpRequest, SignInRequest, EmailConfirmation, ResetPasswordRequest, UserLogin, UserRegistration, UserPasswordReset


router = APIRouter(prefix="/users", tags=["users"])

router.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("user.html", {"request": request})

@router.post("/registration")
async def register_user(user_data: UserRegistration, db: AsyncSession = Depends(get_db)):
    """
    Регистрация нового пользователя
    
    Args:
        user_data: Данные нового пользователя
        db: Сессия базы данных
    """
    try:
        # Проверяем капчу
        from app.utils.captcha import captcha
        is_captcha_valid = captcha.verify_captcha(user_data.captcha_id, user_data.captcha_text)
        
        if not is_captcha_valid:
            return JSONResponse(
                status_code=400,
                content={"detail": "Неверный код с картинки. Пожалуйста, попробуйте еще раз."}
            )
        
        user_service = UserService(db)
        
        # Проверяем, существует ли пользователь с таким email
        existing_user = await user_service.get_by_email(user_data.email)
        if existing_user:
            return JSONResponse(
                status_code=400,
                content={"detail": "Пользователь с таким email уже существует"}
            )
        
        # Создаем нового пользователя
        await user_service.create_user(user_data.email, user_data.password)
        
        # Генерируем токен для подтверждения email
        token = await user_service.create_confirmation_token(user_data.email)
        
        # Отправляем email с токеном для подтверждения
        await send_email(
            to_email=user_data.email,
            subject="Подтверждение регистрации",
            body=f"Для подтверждения регистрации перейдите по ссылке: http://localhost:8000/users/confirm-email?token={token}"
        )
        
        return JSONResponse(
            status_code=200,
            content={"message": "Пользователь успешно зарегистрирован. На ваш email отправлено письмо для подтверждения."}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Ошибка при регистрации: {str(e)}"}
        )

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
async def login(request: Request, response: Response, user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Вход пользователя в систему
    
    Args:
        request: HTTP запрос
        response: HTTP ответ
        user_data: Данные для входа
        db: Сессия базы данных
    """
    try:
        # Проверяем капчу, если она предоставлена
        if user_data.captcha_id and user_data.captcha_text:
            from app.utils.captcha import captcha
            is_captcha_valid = captcha.verify_captcha(user_data.captcha_id, user_data.captcha_text)
            
            if not is_captcha_valid:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Неверный код с картинки. Пожалуйста, попробуйте еще раз."}
                )
        
        user_service = UserService(db)
        
        # Проверяем количество неудачных попыток входа
        login_attempts = await user_service.get_login_attempts(user_data.email)
        
        # Если уже было 3 или более неудачных попыток, и капча не предоставлена
        if login_attempts >= 3 and (not user_data.captcha_id or not user_data.captcha_text):
            return JSONResponse(
                status_code=400,
                content={
                    "detail": "Превышено количество попыток входа. Пожалуйста, введите код с картинки.",
                    "require_captcha": True
                }
            )
        
        # Проверяем учетные данные пользователя
        user = await user_service.authenticate_user(user_data.email, user_data.password)
        
    if not user:
            # Увеличиваем счетчик неудачных попыток входа
            await user_service.increment_login_attempts(user_data.email)
            
            # Проверяем, требуется ли капча для следующей попытки
            login_attempts = await user_service.get_login_attempts(user_data.email)
            
            if login_attempts >= 3:
                return JSONResponse(
                    status_code=400,
                    content={
                        "detail": "Неверный email или пароль",
                        "require_captcha": True
                    }
                )
            
            return JSONResponse(
                status_code=400,
                content={"detail": "Неверный email или пароль"}
            )
        
        # Сбрасываем счетчик неудачных попыток входа
        await user_service.reset_login_attempts(user_data.email)
        
        # Генерируем токены
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Сохраняем refresh_token в базе данных
        await user_service.update_refresh_token(user.email, refresh_token)
        
        # Устанавливаем cookie с токенами
        response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=30*60)
        response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, max_age=7*24*60*60)
        
        return {"message": "Вход выполнен успешно"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Ошибка при входе: {str(e)}"}
        )

@router.get("/captcha")
async def generate_captcha():
    """
    Генерирует новую капчу
    
    Returns:
        dict: Содержит captcha_id и изображение в base64
    """
    from app.utils.captcha import captcha
    return captcha.generate_captcha()

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
async def reset_password(request: Request, user_data: UserPasswordReset, db: AsyncSession = Depends(get_db)):
    """
    Сброс пароля
    
    Args:
        request: HTTP запрос
        user_data: Данные для сброса пароля
        db: Сессия базы данных
    """
    try:
        # Проверяем капчу
        from app.utils.captcha import captcha
        is_captcha_valid = captcha.verify_captcha(user_data.captcha_id, user_data.captcha_text)
        
        if not is_captcha_valid:
            return JSONResponse(
                status_code=400,
                content={"detail": "Неверный код с картинки. Пожалуйста, попробуйте еще раз."}
            )
            
        user_service = UserService(db)
    refresh_token = request.cookies.get("refresh_token")
        
        if refresh_token:
            # Пользователь авторизован, используем его токен для сброса
            user = await user_service.update_password(refresh_token=refresh_token, password=user_data.password)
            if user is None:
                # Если токен недействителен, пробуем использовать email
                if user_data.email:
                    await user_service.update_password(user_data.email, user_data.password)
                    return {"message": "Пароль успешно обновлен"}
                else:
                    return JSONResponse(
                        status_code=404, 
                        content={"detail": "Пользователь не найден"}
                    )
        else:
            # Пользователь не авторизован, используем email и старый пароль
            if not user_data.email:
                return JSONResponse(
                    status_code=400, 
                    content={"detail": "Email обязателен, если вы не авторизованы"}
                )
                
            user = await user_service.get_by_email(user_data.email)
            if user is None:
                return JSONResponse(
                    status_code=404, 
                    content={"detail": "Пользователь не найден"}
                )
                
            if not user_data.old_password:
                return JSONResponse(
                    status_code=400, 
                    content={"detail": "Старый пароль обязателен, если вы не авторизованы"}
                )
                
            if not verify_password(user_data.old_password, user.hashed_password):
                return JSONResponse(
                    status_code=400, 
                    content={"detail": "Неверный старый пароль"}
                )
                
            await user_service.update_password(user_data.email, user_data.password)
            
        return {"message": "Пароль успешно обновлен"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Ошибка при сбросе пароля: {str(e)}"}
        )