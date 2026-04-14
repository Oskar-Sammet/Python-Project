import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.database import engine, Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        pass

    # Verify database connectivity
    async with engine.connect() as conn:
        logger.info(f"Database connection verified")

    yield

    await engine.dispose()
    logger.info(f"Database connection closed")

