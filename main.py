from fastapi import FastAPI, Request

from src.database.postgres import create_table
from src.routers import files

app = FastAPI()
# create_table()

app.include_router(files.router)