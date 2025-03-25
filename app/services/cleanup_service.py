from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select
from datetime import datetime, timedelta
from app.domain.models.database import get_db, AsyncSessionLocal
from app.domain.models.user import Users
from sqlalchemy.ext.asyncio import AsyncSession

class CleanupService:
    def __init__(self):
        self.scheduler = None

    async def start(self):
        """Запускает планировщик"""
        if self.scheduler is None:
            self.scheduler = AsyncIOScheduler()
            self.scheduler.add_job(
                self.cleanup_expired_users,
                trigger=IntervalTrigger(minutes=10),
                id='cleanup_expired_users'
            )
            self.scheduler.start()

    async def cleanup_expired_users(self):
        async with AsyncSessionLocal() as db:
            current_time = datetime.utcnow()
            query = select(Users).where(
                (Users.confirmed == False) & 
                (Users.expires_at < current_time)
            )
            result = await db.execute(query)
            expired_users = result.scalars().all()
            
            for user in expired_users:
                await db.delete(user)
            
            await db.commit()

    async def stop(self):
        """Останавливает планировщик"""
        if self.scheduler:
            self.scheduler.shutdown()
            self.scheduler = None 