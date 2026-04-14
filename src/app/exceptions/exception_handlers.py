from fastapi import FastAPI, Request
import logging

from datetime import datetime
from starlette.responses import JSONResponse

from src.app.exceptions.exceptions import ConflictException, BaseAppException, NotFoundException, TypeNotSupportedException
from src.schemas.responses import ErrorResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def register_exception_handlers(app: FastAPI):
    """Register exception handlers"""

    @app.exception_handler(BaseAppException)
    async def base_app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
        logger.error("Application error: %s", exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
            error=exc.message,
            code=f"APP_ERROR_{exc.status_code}",
            timestamp=datetime.now(),
            path=str(request.url.path),
        ).model_dump())

    @app.exception_handler(ConflictException)
    async def conflict_exception_handler(request: Request, exc: ConflictException) -> JSONResponse:
        logger.error("Conflict error: %s", exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=exc.message,
                code=f"CONFLICT_{exc.status_code}",
                timestamp=datetime.now(),
                path=str(request.url.path),
            ).model_dump()
        )

    @app.exception_handler(NotFoundException)
    async def not_found_exception_handler(request: Request, exc: NotFoundException) -> JSONResponse:
        logger.error("Not found: %s", exc.message)
        return JSONResponse(status_code=exc.status_code, content=ErrorResponse(
            error=exc.message,
            code=f"MISSING_{exc.status_code}",
            timestamp=datetime.now(),
            path=str(request.url.path),
        ).model_dump())

    @app.exception_handler(TypeNotSupportedException)
    async def type_not_supported_exception_handler(request: Request, exc: NotFoundException) -> JSONResponse:
        logger.error("Not supported: %s", exc.message)
        return JSONResponse(status_code=exc.status_code, content=ErrorResponse(
            error=exc.message,
            code=f"NOT_SUPPORTED_{exc.status_code}",
            timestamp=datetime.now(),
            path=str(request.url.path),
        ).model_dump())