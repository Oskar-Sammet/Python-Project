from fastapi import FastAPI, Request
from src.routers import files

app = FastAPI()

#create_table()

app.include_router(files.router)
