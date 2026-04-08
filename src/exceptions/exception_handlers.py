from starlette.responses import JSONResponse

from src.exceptions.exceptions import FileNotFoundException, BaseAppException, FileConflictException
from main import app
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.exception_handler(BaseAppException)
async def base_app_exception_handler(request, exc) -> JSONResponse:
    logger.error("Application error: %s", exc.message)
    return JSONResponse(status_code=exc.status_code, content={"message": exc.message})

@app.exception_handler(FileConflictException)
async def file_conflict_exception_handler(request, exc) -> JSONResponse:
    logger.error("File conflict error: %s", exc.message)
    return JSONResponse(status_code=409, content={"message": exc.message})

@app.exception_handler(FileNotFoundException)
async def file_conflict_exception_handler(request, exc) -> JSONResponse:
    logger.error("File conflict error: %s", exc.message)
    return JSONResponse(status_code=409, content={"message": exc.message})