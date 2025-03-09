# app/models/user.py
from sqlalchemy import Column, Integer, String, VARCHAR
from app.database import Base
from sqlalchemy.orm import relationship
from schemas.user import Base 


class Users(Base):
    __tablename__ = "users"

    username = Column(String, unique=True, index=True)
    email = Column(String, primary_key=True, unique=True, index=True)
    hashed_password = Column(VARCHAR(255), index=True)

    items = relationship("Item", back_populates="owner")

# app/schemas/user.py
from pydantic import BaseModel, EmailStr

class SignUpRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        orm_mode = True
