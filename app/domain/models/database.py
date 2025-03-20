from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from migrations.database.env import username, password, host, dbname

DATABASE_URL = f"postgresql+asyncpg://{quote_plus(username)}:{quote_plus(password)}@{host}/{dbname}"

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

async def get_db():
    session = SessionLocal()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    