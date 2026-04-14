from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.database.database import Session

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = Session()
    app.state.db = db

    app.state.test = 50

    yield

    db.close()
