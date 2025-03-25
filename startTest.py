import asyncio
import tracemalloc
from tests.test_analysis import test_analysis_service
from migrations.database.main import PostgresDB

tracemalloc.start()

async def start():
    await test_analysis_service()

if __name__ == '__main__':
    PostgresDB()
    asyncio.run(start())