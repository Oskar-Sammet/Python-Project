from fastapi import APIRouter, UploadFile, Depends
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from src.repositories.file_repository import FileRepository
from src.dependencies import get_database_session
from src.models.file import File
from src.exceptions.exceptions import ErrorResponse
from src.schemas.file import FileStatusEnum, FileRead
from src.schemas.responses import MessageResponse, SearchResponse
from src.services import file_service
from src.services.file_service import DEFAULT_FILE_LIMIT, DEFAULT_START_SKIP
from src.utils.validators import FileValidator

router = APIRouter(
    prefix="/files",
    tags=["files"],
)

upload_validator = FileValidator()

_error_responses = {
    404: { "model": ErrorResponse, "description": "Resource not found" },
    500: { "model": ErrorResponse, "description": "Internal server error" },
}

def get_file_repository(session: AsyncSession = Depends(get_database_session)) -> FileRepository:
    return FileRepository(session)

@router.get("/query", response_model=SearchResponse, responses={
    500: { "model": ErrorResponse, "description": "Internal server error" }
})
def search(query: str) -> JSONResponse:
    results = file_service.search(query)
    return JSONResponse(status_code=200, content={"answer": results})

# Get a paginated list of processed files with filtering
@router.get("/", response_model=List[FileRead], responses={
    500: { "model": ErrorResponse, "description": "Internal server error" }
})
async def get_files(
        status: FileStatusEnum = FileStatusEnum.COMPLETED,
        skip: int = DEFAULT_START_SKIP,
        limit: int = DEFAULT_FILE_LIMIT,

        repo: FileRepository = Depends(get_file_repository),
) -> list[File]:
    return await file_service.get_files_filtered(status, skip, limit, repo)

# Get a specific processed file by ID
@router.get("/{file_id}", response_model=FileRead, responses=_error_responses)
async def get_file(file_id: int, repo: FileRepository = Depends(get_file_repository)) -> File:
    return await file_service.get_file_by_id(file_id, repo)

# Route for uploading files
@router.post("/", response_model=MessageResponse, responses={
    500: { "model": ErrorResponse, "description": "Internal server error" }
})
async def upload_file(uploaded_file: UploadFile, repo: FileRepository = Depends(get_file_repository)) -> JSONResponse:
    await file_service.upload_file(uploaded_file, repo)
    return JSONResponse(status_code=200, content={"message": "File uploaded successfully"})

# Route for processing one specific file
@router.post("/process/{file_id}", response_model=MessageResponse, responses=_error_responses)
async def process_file(file_id: int, repo: FileRepository = Depends(get_file_repository)) -> JSONResponse:
    await file_service.process_file_by_id(file_id, repo)
    return JSONResponse(status_code=200, content={"message": "File processed successfully"})

# Route for processing multiple files
@router.post("/process", response_model=MessageResponse, responses=_error_responses)
async def process_files(file_ids: List[int], repo: FileRepository = Depends(get_file_repository)) -> JSONResponse:
    file_service.process_files_by_ids(file_ids, repo)
    return JSONResponse(status_code=200, content={"message": "Files processed successfully"})
