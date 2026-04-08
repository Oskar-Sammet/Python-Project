from datetime import datetime
from pydantic import BaseModel, ConfigDict

# DTO
class FileBase(BaseModel):
    filename: str
    content: str

    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    model_config = ConfigDict(from_attributes=True)

class FileCreate(FileBase):
    pass

class FileSchema(FileBase):
    id: int