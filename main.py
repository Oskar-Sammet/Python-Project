from fastapi import FastAPI
from src.routers import files
from src.exceptions.exception_handlers import register_exception_handlers

app = FastAPI()

# create_table()
register_exception_handlers(app)

app.include_router(files.router)
