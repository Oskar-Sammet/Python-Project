import os
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from typing import Annotated, List

from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from src.exceptions.exceptions import FileNotFoundException
from src.schemas.file import FileStatusEnum
from src.database.postgres import get_db
from src.services import file_service
from src.utils.validators import FileValidator
from src.schemas.file import FileSchema, FileListItem, FileCreate
from src.config import settings

router = APIRouter(
    prefix="/files",
    tags=["files"],
)

upload_validator = FileValidator()

# Get a specific processed file by ID
@router.get("/{file_id}")
async def get_processed_file(file_id: int):
    pass

# Get a paginated list of processed files with filtering
@router.get("/", response_model=List[FileListItem])
async def get_processed_files(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return file_service.get_files(skip, limit, db)

# Route for uploading files
@router.post("/", response_model=FileSchema)
async def upload_file(uploaded_file: Annotated[UploadFile, File()], db: Session = Depends(get_db)):
    # Validate the files extension and content type
    await upload_validator.validate(uploaded_file)

    os.makedirs(settings.UPLOAD_DESTINATION, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DESTINATION, uploaded_file.filename)

    with open(file_path, "wb") as buffer:
        content = await uploaded_file.read()
        buffer.write(content)

    # Create a FileCreate instance from the uploaded file using the mapper
    file_create = FileCreate(filename=uploaded_file.filename,
                             status=FileStatusEnum.ready, path=file_path)

    # Upload the file to the database
    file = file_service.upload_file(file_create, db)

    # Close the file
    await uploaded_file.close()

    if not file:
        raise FileNotFoundException("File upload failed!")

    return file

# Route for processing one specific file
# Get a local path -> Process -> vector database
@router.post("/process/{file_id}")
async def process_file(file_id: int, db: Session = Depends(get_db)):
    file_service.process_file(file_id, db)
    return JSONResponse(status_code=200, content={"message": "File processed successfully"})

# Route for processing multiple files
@router.post("/process")
async def process_files(file_ids: Annotated[List[int], int], db: Session = Depends(get_db)):
    for file_id in file_ids:
        file_service.process_file(file_id, db)
    return JSONResponse(status_code=200, content={"message": "Files processed successfully"})