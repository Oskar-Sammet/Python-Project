from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Enum, LargeBinary
from src.database.postgres import Base
from src.schemas.file import FileStatusEnum

# Entity
class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String, index=True, unique=True)
    path = Column(String, index=True)

    status = Column(Enum(FileStatusEnum), default=FileStatusEnum.ready)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)