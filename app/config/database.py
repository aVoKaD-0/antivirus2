import asyncpg
import asyncio

class AsyncPostgresDB:
    def __init__(self, dsn):
        self.dsn = dsn
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(self.dsn)

    async def execute(self, query, params=None, fetch=False):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                result = await conn.fetch(query, *params) if fetch else await conn.execute(query, *params)
                return result if fetch else None

    async def close(self):
        await self.pool.close()

async def main():
    db = AsyncPostgresDB("postgresql://almaz:almaz@localhost/5432")
    await db.connect()

    # await db.execute("INSERT INTO users (name, age) VALUES ($1, $2)", ("Charlie", 22))
    users = await db.execute("SELECT * FROM users", fetch=True)
    print(users)

    await db.close()

asyncio.run(main())
