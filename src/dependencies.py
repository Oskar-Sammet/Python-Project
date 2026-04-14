from typing import AsyncGenerator
from contextlib import asynccontextmanager
from .database import async_session_factory

from fastapi import Request

async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            pass

@asynccontextmanager
async def get_database_session_context() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            pass
