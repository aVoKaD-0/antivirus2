from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models.user import Users
from app.core.security import get_password_hash
from sqlalchemy import select
from app.auth.auth import generate_code

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str):
        result = await self.db.execute(select(Users).filter(Users.email == email))
        return result.scalars().first()
    
    # async def get_user_by_hashed_password(self, hashed_password: str):
    #     result = await self.db.execute(select(Users).filter(Users.hashed_password == hashed_password))
    #     return result.scalars().first()

    async def create_user(self,  email: str, password: str):
        hashed_password = get_password_hash(password)
        confiration_code = generate_code()
        new_user = Users(email=email, hashed_password=hashed_password, confiration_code=confiration_code)
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user, confiration_code
    
    async def __commit__(self):
        await self.db.commit()