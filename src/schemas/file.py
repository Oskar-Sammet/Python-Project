from enum import Enum
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class FileStatusEnum(str, Enum):
    READY = "ready"
    COMPLETED = "completed"

class FileBase(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    path: str = Field(min_length=1, max_length=255)
    status: FileStatusEnum

class FileRead(FileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime