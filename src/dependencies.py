from typing import AsyncGenerator
from contextlib import asynccontextmanager
from .database import session_factory, scoped_session
from sqlalchemy.ext.asyncio import AsyncSession

async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    async with scoped_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            pass

@asynccontextmanager
async def get_database_session_context() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            pass
