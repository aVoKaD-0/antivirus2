from sqlalchemy import select
from app.domain.models.database import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from migrations.database.db.models import Results, Analysis

class AnalysisDbService:
    async def get_database(self):
        db = AsyncSessionLocal()
        return db
    
    async def get_result(self, analysis_id: str, db: AsyncSession):
        result = await db.execute(
            select(Results).filter(Results.analysis_id == analysis_id)
        )
        return result.scalars().first()

    async def get_analysis(self, analysis_id, db: AsyncSession):
        result = await db.execute(select(Analysis).filter(Analysis.analysis_id == analysis_id))
        return result.scalars().first()