from pydantic import BaseModel
from pydantic import EmailStr


class SingUpRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class SingUpResponse(BaseModel):
    id: int
    token: str

class SignInRequest(BaseModel):
    username: str
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