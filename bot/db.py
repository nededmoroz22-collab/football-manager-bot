import os
import asyncio
import asyncpg

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/postgres")

_pool = None

async def init_db_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    return _pool

def get_pool():
    if _pool is None:
        raise RuntimeError("DB pool not initialized. Call init_db_pool on startup.")
    return _pool