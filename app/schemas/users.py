from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    captcha_id: Optional[str] = None
    captcha_text: Optional[str] = None

class UserRegistration(BaseModel):
    email: EmailStr
    password: str
    captcha_id: str
    captcha_text: str

class UserPasswordReset(BaseModel):
    email: str
    password: Optional[str] = None
    old_password: Optional[str] = None
    captcha_id: Optional[str] = None
    captcha_text: Optional[str] = None 