from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from urllib.parse import quote_plus
from migrations.database.env import username, password, host, dbname
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from sqlalchemy.orm import sessionmaker

# 🔥 Подключение к БД
DATABASE_URL = f"postgresql+asyncpg://{quote_plus(username)}:{quote_plus(password)}@{host}/{dbname}"

# 🔥 Создаём асинхронный движок
engine = create_async_engine(DATABASE_URL, echo=True)

# 🔥 Создаём асинхронную фабрику сессий
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 🔥 Функция для получения сессии
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session  # ✅ FastAPI сам закроет соединение
