from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from database.env import username, password, host, dbname

DATABASE_URL = f"postgresql://{quote_plus(username)}:{quote_plus(password)}@{host}/{dbname}"

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

async def get_db():
    async with SessionLocal() as session:
        yield session
    