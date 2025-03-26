from pydantic import EmailStr
from pydantic import BaseModel
from typing import Optional

class SingUpRequest(BaseModel):
    email: str
    password: str

class SingUpResponse(BaseModel):
    id: int
    token: str

class SignInRequest(BaseModel):
    email: str
    password: str

class SignInResponse(BaseModel):
    id: int
    token: str

class UserUpdateRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserUpdateResponse(BaseModel):
    id: int
    token: str

class UserDeleteRequest(BaseModel):
    id: int
    token: str 

class UserDeleteResponse(BaseModel):
    status: bool

class EmailConfirmation(BaseModel):
    code: str

class ResetPasswordRequest(BaseModel):
    password: str
    email: str = None
    old_password: str = None

class ResetPasswordResponse(BaseModel):
    status: bool

class UserLogin(BaseModel):
    email: str
    password: str
    captcha_id: Optional[str] = None
    captcha_text: Optional[str] = None

class UserRegistration(BaseModel):
    email: str
    password: str
    captcha_id: str
    captcha_text: str

class UserPasswordReset(BaseModel):
    email: str
    password: str
    captcha_id: str
    captcha_text: str
    old_password: Optional[str] = None