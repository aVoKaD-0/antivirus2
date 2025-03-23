from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from captcha.image import ImageCaptcha
from random import choices
import string
from app.config.auth import SECRET_KEY, ALGORITHM, REFRESH_TOKEN_EXPIRE_DAYS, ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi_mail import FastMail, MessageSchema
from app.config.auth import SMTP
# Секретный ключ для подписи токенов
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# === Генерация токена ===
def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def uuid_by_token(token: str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    uuid = payload.get("sub")
    return uuid

# === Хэширование пароля ===
# def hash_password(password: str):
#     return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# === Генерация кода подтверждения ===
def generate_code():
    return ''.join(choices(string.digits, k=6))

def generate_captcha():
    captcha = ImageCaptcha()
    text = ''.join(choices(string.ascii_letters + string.digits, k=6))
    captcha.write(text, "captcha.png")
    return {"captcha": text}

async def verify_token(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username

def refresh_token(token: str = Depends(oauth2_scheme)):
    print(token)
    payload = jwt.decode(token=token, key=SECRET_KEY, algorithms=[ALGORITHM])
    print(payload)
    uuid = payload.get("sub")
    return uuid

async def send_email(email: str, body: str):
    message = MessageSchema(
        subject="Confirm your account",
        recipients=[email],
        body=body,
        subtype="plain"
    )

    fm = FastMail(SMTP)
    await fm.send_message(message)

# async def get_current_user(request: Request):
#     access_token = request.cookies.get("access_token")
#     refresh_token = request.cookies.get("refresh_token")
#     if not access_token and not refresh_token:
#         raise HTTPException(status_code=401, detail="Not authenticated")
    
#     try:
#         payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
#         email = payload.get("sub")
#         if email is None:
#             raise HTTPException(status_code=401, detail="Invalid token")
#         payload2 = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
#         username = payload2.get("sub")
#         if username is None:
#             token = create_access_token({"sub": email}, timedelta(minutes=15))
#             request.cookies["access_token"] = token
#             return email
#         return username
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid token")