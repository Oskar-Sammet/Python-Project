from datetime import datetime

from sqlalchemy import String, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base
from src.schemas.file import FileStatusEnum

# Entity
class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)

    filename: Mapped[str] = mapped_column(String(255), index=True, unique=True)
    path: Mapped[str] = mapped_column(String(512), index=True)

    status: Mapped[FileStatusEnum] = mapped_column(Enum(FileStatusEnum, values_callable=lambda x: [e.value for e in x]))

    created_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=True)

    def __repr__(self) -> str:
        return f"<File: {self.filename}>"