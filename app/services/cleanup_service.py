from sqlalchemy import select
from datetime import datetime
from app.domain.models.user import Users
from apscheduler.triggers.interval import IntervalTrigger
from app.domain.models.database import AsyncSessionLocal
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class CleanupService:
    def __init__(self):
        self.scheduler = None

    async def start(self):
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
        if self.scheduler:
            self.scheduler.shutdown()
            self.scheduler = None 