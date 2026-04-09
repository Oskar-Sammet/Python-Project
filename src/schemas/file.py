import enum
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class FileStatusEnum(enum.Enum):
    ready = 0
    processing = 1
    completed = 2

class FileBase(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    path: str = Field(min_length=1, max_length=255)
    status: FileStatusEnum

class FileCreate(FileBase):
    pass

class FileRead(FileBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
