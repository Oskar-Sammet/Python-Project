from typing import Annotated

from fastapi import UploadFile, File

from src.schemas.file import FileCreate
from src.utils.docling import extract_content

async def from_upload_file_to_file_create(upload_file: Annotated[UploadFile, File()]) -> FileCreate:
    file_bytes = await upload_file.read()
    content = extract_content(file_bytes, upload_file.filename)

    return FileCreate(filename=upload_file.filename, content=content)
