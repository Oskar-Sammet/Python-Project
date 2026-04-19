from typing import TypeVar, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.file import FileStatusEnum
from src.database import Base
from src.models.file import File
from .base_repository import BaseRepository

ModelType = TypeVar("ModelType", bound=Base)

class FileRepository(BaseRepository[File]):
    def __init__(self, session: AsyncSession):
        super().__init__(File, session)

    async def get_filtered_files(self, status: FileStatusEnum, skip: int, limit: int) -> List[File]:
        query = select(self.model).where(self.model.status == status.value).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_status(self, file_id: int, status: FileStatusEnum) -> None:
        query = update(File).where(self.model.id == file_id).values(status=status)
        await self.session.execute(query)