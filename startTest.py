from tests.test import test_analysis_service
import asyncio
import tracemalloc
tracemalloc.start()
from migrations.database.main import PostgresDB

async def start():
    await test_analysis_service()

if __name__ == '__main__':
    PostgresDB()
    asyncio.run(start())