import os
import asyncpg
from typing import Optional


class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self, dsn: str | None = None):
        dsn = dsn or os.getenv("DATABASE_URL")
        if not dsn:
            raise ValueError(
                "DATABASE_URL no está definida. "
                "Ponla en .env o en la variable de entorno."
            )
        self.pool = await asyncpg.create_pool(
            dsn, min_size=2, max_size=10, ssl="require"
        )

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def fetch(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def execute(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def transaction(self):
        """Returns an async context manager for a transactional connection.
        Usage: async with db.transaction() as conn: await conn.execute(...)
        """
        class _Transaction:
            def __init__(self, pool):
                self.pool = pool
                self.conn = None
            async def __aenter__(self):
                self.conn = await self.pool.acquire()
                await self.conn.execute("BEGIN")
                return self.conn
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                if exc_type is None:
                    await self.conn.execute("COMMIT")
                else:
                    await self.conn.execute("ROLLBACK")
                await self.pool.release(self.conn)
        return _Transaction(self.pool)
