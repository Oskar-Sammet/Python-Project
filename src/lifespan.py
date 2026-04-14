from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        pass

    # Verify database connectivity
    async with engine.connect() as conn:
        print("Database connection verified")

    yield

    await engine.dispose()
    print("Database connection closed")

