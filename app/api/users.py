from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_service import UserService
# from repositories.user_repository import UserRepository
from app.domain.models.database import User
from app.schemas import user as user_schema
from app.schemas.user import SignUpRequest

UserResponse = user_schema.UserResponse
UserCreate = user_schema.UserCreate

router = APIRouter(prefix="/users", tags=["users"])

# Функция для получения сессии БД
async def get_db():
    async with User() as session:
        yield session

# Эндпоинт для создания пользователя
@router.post("/", response_model=UserResponse)
async def SignUp(user: SignUpRequest, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    created_user = await user_service.create_user(user.username, user.email, user.password)
    return created_user
    return None

# Эндпоинт для получения пользователя по ID
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    # user_service = UserService(db)
    # user = await user_service.get_user(user_id)
    # if not user:
    #     raise HTTPException(status_code=404, detail="User not found")
    # return user
    return None

# Эндпоинт для получения всех пользователей
@router.get("/", response_model=List[UserResponse])
async def get_users(db: AsyncSession = Depends(get_db)):
    # user_service = UserService(db)
    # users = await user_service.get_all_users()
    # return users
    return None
