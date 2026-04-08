from fastapi import FastAPI

from src.database.postgres import create_table
from src.routers import files

app = FastAPI()
# create_table()

app.include_router(files.router)

from src.exceptions import exception_handlers  # noqa: E402, F401