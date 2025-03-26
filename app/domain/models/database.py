from typing import AsyncGenerator
from urllib.parse import quote_plus
from sqlalchemy.ext.asyncio import AsyncSession
from migrations.database.env import username, password, host, dbname
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

DATABASE_URL = f"postgresql+asyncpg://{quote_plus(username)}:{quote_plus(password)}@{host}/{dbname}"

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session 
