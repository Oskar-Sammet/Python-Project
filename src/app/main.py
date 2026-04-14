from fastapi import FastAPI

from src.lifespan import lifespan
from src.app.routers import files
from src.app.exceptions.exception_handlers import register_exception_handlers

app = FastAPI(lifespan=lifespan)

register_exception_handlers(app)

app.include_router(files.router)

