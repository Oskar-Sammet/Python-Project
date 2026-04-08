from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
import enum

class FileStatusEnum(enum.Enum):
    ready = 0
    processing = 1
    completed = 2

# DTO
class FileBase(BaseModel):
    filename: str
    path: str

    status: enum.Enum

    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    model_config = ConfigDict(from_attributes=True)

class FileCreate(FileBase):
    pass

class FileSchema(FileBase):
    id: int

class FileListItem(BaseModel):
    id: int
    filename: str

    status: enum.Enum

    model_config = ConfigDict(from_attributes=True)