from fastapi import APIRouter, UploadFile, File, Depends, Query
from typing import Annotated, List, Optional
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from src.schemas.file import FileStatusEnum
from src.schemas.file import FileRead
from src.database.postgres import get_db
from src.services import file_service
from src.utils.validators import FileValidator

router = APIRouter(
    prefix="/files",
    tags=["files"],
)

upload_validator = FileValidator()

@router.get("/query")
def search(query: str, db: Session = Depends(get_db)):
    results = file_service.search(query, db)

    print(results)

    # for hit in results:
    #     print(f"score={hit.score:.4f}  id={hit.id}  chunk_index={hit.payload.get('chunk_index')}")

    return JSONResponse(status_code=200, content={"message": "Files processed successfully"})

# Get a paginated list of processed files with filtering
@router.get("/", response_model=List[FileRead])
async def get_files(
        status: Optional[FileStatusEnum] = None,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        db: Session = Depends(get_db)
):
    return file_service.get_files(status, skip, limit, db)

# Get a specific processed file by ID
@router.get("/{file_id}", response_model=FileRead)
async def get_file(file_id: int, db: Session = Depends(get_db)):
    return file_service.get_file(file_id, db)


# Route for uploading files
@router.post("/")
async def upload_file(uploaded_file: Annotated[UploadFile, File()], db: Session = Depends(get_db)):
    await file_service.upload_file(uploaded_file, db)
    return JSONResponse(status_code=200, content={"message": "File uploaded successfully"})

# Route for processing one specific file
# Get a local path -> Process -> vector database
@router.post("/process/{file_id}")
async def process_file(file_id: int, db: Session = Depends(get_db)):
    file_service.process_file(file_id, db)
    return JSONResponse(status_code=200, content={"message": "File processed successfully"})

# Route for processing multiple files
@router.post("/process")
async def process_files(file_ids: Annotated[List[int], int], db: Session = Depends(get_db)):
    file_service.process_files(file_ids, db)
    return JSONResponse(status_code=200, content={"message": "Files processed successfully"})