"""Abstract interfaces for dependency inversion (DIP)."""

from typing import Any, AsyncContextManager, Optional, Protocol, runtime_checkable


@runtime_checkable
class DatabaseInterface(Protocol):
    """Abstract data access interface — enables swapping asyncpg for other drivers."""

    async def fetch(self, query: str, *args) -> list[Any]:
        ...

    async def fetchrow(self, query: str, *args) -> Optional[Any]:
        ...

    async def execute(self, query: str, *args) -> str:
        ...

    async def transaction(self) -> AsyncContextManager[Any]:
        ...
