from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models.user import Users
from app.core.security import get_password_hash
from sqlalchemy import select

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str):
        result = await self.db.execute(select(Users).filter(Users.email == email))
        return result.scalars().first()

    async def create_user(self, username: str, email: str, password: str):
        hashed_password = get_password_hash(password)
        new_user = Users(username=username, email=email, hashed_password=hashed_password)
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user