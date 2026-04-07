from fastapi import HTTPException, UploadFile
from typing import Set

import magic

class FileValidator:
    def __init__(self, allowed_extensions: Set[str] = None, allowed_content_types: Set[str] = None):
        self.allowed_extensions = allowed_extensions or {
            ".txt", ".md", ".pdf", ".csv"
        }
        self.allowed_content_types = allowed_content_types or {
            "text/plain", "text/markdown", "application/pdf", "text/csv"
        }

    async def validate(self, file: UploadFile) -> str:
        """ Run all validations on the uploaded file."""
        extension = await self._validate_extension(file)
        await self._validate_content_type(file)

        return extension

    async def _validate_extension(self, file: UploadFile) -> str:
        extension = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""

        if extension not in self.allowed_extensions:
            raise HTTPException(status_code=400, detail="Invalid file extension")

        return extension

    async def _validate_content_type(self, file: UploadFile) -> None:
        header = await file.read(2048)
        await file.seek(0)

        detected_type = magic.from_buffer(header, mime=True)

        if detected_type not in self.allowed_content_types:
            raise HTTPException(status_code=400, detail=f"Content type '{detected_type}' not allowed. Allowed: {self.allowed_content_types}")