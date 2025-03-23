from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models.database import get_db
from sqlalchemy import select
from migrations.database.db.models import Results, Analysis
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

class AnalysisDbService:
    # def __init__(self):
    #     self._session = None

    # async def get_db(self) -> AsyncSession:
    #     if not self._session:
    #         self._session = await get_db()
    #     yield self._session

    # async def commit(self, db: AsyncSession):
    #     await db.commit()
    #     return

    # async def close(self, db: AsyncSession):
    #     await db.close()
    #     return

    # async def add(self, model, db: AsyncSession):
    #     db.add(model)
    #     await db.commit()
    #     return

    #  дубль с user_service
    async def get_user_analyses(self, user_id: str, db: AsyncSession):
        result = await db.execute(
            select(Analysis.timestamp, Analysis.filename, Analysis.status)
            .filter(Analysis.user_id == user_id)
        )
        return result.all()
    
    async def get_result(self, analysis_id: str, db: AsyncSession):
        result = await db.execute(
            select(Results).filter(Results.analysis_id == analysis_id)
        )
        return result.scalars().first()

    async def get_analysis(self, analysis_id, db: AsyncSession):
        result = await db.execute(select(Analysis).filter(Analysis.analysis_id == analysis_id))
        return result.scalars().first()
    
    # async def save_activity(self, analysis_id, file_activity, db: AsyncSession):
    #     result = await db.execute(
    #         select(Results).filter(Results.analysis_id == analysis_id)
    #     )
    #     result_obj = result.scalars().first()
    #     if result_obj:
    #         result_obj.file_activity = file_activity
    #         await db.commit()

    # async def save_result(self, analysis_id, result_data, db: AsyncSession):
    #     result = await db.execute(
    #         select(Results).filter(Results.analysis_id == analysis_id)
    #     )
    #     result_obj = result.scalars().first()
    #     if result_obj:
    #         result_obj.results = result_data
    #         db.add(result_obj)
    #         await db.commit()

    # async def __refresh__(self, db: AsyncSession):
    #     await db.refresh()