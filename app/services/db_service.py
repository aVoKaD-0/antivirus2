from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models.database import get_db
from sqlalchemy import select
from migrations.database.db.models import Results, Analysis

class AnalysisDbService:
    def __init__(self):
        self._session = None

    async def get_db(self) -> AsyncSession:
        if not self._session:
            async for session in get_db():
                self._session = session
                return session
        return self._session

    async def get_user_analyses(self, user_id: str):
        async with await self.get_db() as session:
            result = await session.execute(
                select(Analysis.timestamp, Analysis.filename, Analysis.status)
                .filter(Analysis.user_id == user_id)
            )
            return result.all()
    
    async def get_result(self, analysis_id: str):
        async with await self.get_db() as session:
            result = await session.execute(
                select(Results).filter(Results.analysis_id == analysis_id)
            )
            return result.scalars().first()
    
    async def commit(self):
        if self._session:
            await self._session.commit()

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None

    async def add(self, model):
        async with await self.get_db() as session:
            session.add(model)
            await session.commit()
            return model

    async def ger_analysis(self, analysis_id):
        async with await self.get_db() as session:
            result = await session.execute(select(Analysis).filter(Analysis.analysis_id == analysis_id))
            return result.scalars().first()
    
    async def save_activity(self, analysis_id, file_activity):
        async with await self.get_db() as session:
            result = await session.execute(
                select(Results).filter(Results.analysis_id == analysis_id)
            )
            result_obj = result.scalars().first()
            if result_obj:
                result_obj.file_activity = file_activity
                await session.commit()

    async def __refresh__(self):
        if self._session:
            await self._session.refresh()