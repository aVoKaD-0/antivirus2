from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.services.user_service import UserService
# # from repositories.user_repository import UserRepository
# from app.schemas.user import SingUpRequest, SingUpResponse
# from app.domain.models.database import get_db


router = APIRouter(prefix="/users", tags=["users"])

# router.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("user.html", {"request": request})

# Эндпоинт для создания пользователя
# @router.post("/register")
# async def SignUp(user: SingUpRequest, db: AsyncSession = Depends(get_db)):
#     user_service = UserService(db)
#     existing_user = await user_service.get_user_by_email(user.email)
#     if existing_user:
#         raise HTTPException(status_code=400, detail="Email already registered")
#     created_user = await user_service.create_user(user.username, user.email, user.password)
#     return created_user

# # Эндпоинт для получения пользователя по ID
# @router.get("/{user_id}", response_model=UserResponse)
# async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
#     # user_service = UserService(db)
#     # user = await user_service.get_user(user_id)
#     # if not user:
#     #     raise HTTPException(status_code=404, detail="User not found")
#     # return user
#     return None

# # Эндпоинт для получения всех пользователей
# @router.get("/", response_model=List[UserResponse])
# async def get_users(db: AsyncSession = Depends(get_db)):
#     # user_service = UserService(db)
#     # users = await user_service.get_all_users()
#     # return users
#     return None
