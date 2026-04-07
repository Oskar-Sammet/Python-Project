
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from typing import Annotated, List

from sqlalchemy.orm import Session

from src.database.postgres import get_db
from src.database.mapper.file_mapper import from_upload_file_to_file_create
from src.database.services import file_service
from src.utils.validators import FileValidator
from src.database.schemas.file import FileSchema
import ollama

router = APIRouter(
    prefix="/files",
    tags=["files"],
)

upload_validator = FileValidator()

# Get a specific processed file by ID
@router.get("/process/{file_id}")
async def get_processed_file(file_id: int):
    pass

# Get a paginated list of processed files with filtering
@router.get("/", response_model=List[FileSchema])
async def get_processed_files(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return file_service.get_files(skip, limit, db)

# Route for uploading files
@router.post("/", response_model=FileSchema)
async def upload_file(uploaded_file: Annotated[UploadFile, File()], db: Session = Depends(get_db)):
    # Validate the files extension and content type
    extension = await upload_validator.validate(uploaded_file)

    # if extension == ".pdf":
    #     print("PDF detected")
    #     raise HTTPException(status_code=400, detail="PDF files are not supported yet!")

    file = file_service.upload_file(await from_upload_file_to_file_create(uploaded_file), db)

    if not file:
        raise HTTPException(status_code=404, detail="File not found!")

    await uploaded_file.close()

    return file

# Route for processing one specific file
@router.post("/process/{id}")
async def process_file(file_id: int, db: Session = Depends(get_db)):
    file_service.process_file(file_id, db)
    return {"status": 200}

# Route for processing multiple files
@router.post("/process")
async def process_files():
    pass