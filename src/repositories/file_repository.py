from sqlalchemy.orm import Session

from src.dependencies import DatabaseDep
from src.models.file import File
from src.schemas.file import FileStatusEnum

class FileRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, file_id: int) -> File | None:
        return self.db.query(File).filter(File.id == file_id).first()

    def get_filtered_files(self, status: FileStatusEnum | None, skip: int, limit: int) -> list[type[File]]:
        query = self.db.query(File)
        if status is not None:
            query = query.filter(File.status == str(status.value))
        return query.offset(skip).limit(limit).all()

    def create(self, file_instance: File) -> File:
        self.db.add(file_instance)
        self.db.commit()
        self.db.refresh(file_instance)
        return file_instance

    def update_status(self, file_id: int, status: FileStatusEnum) -> None:
        self.db.query(File).filter(File.id == file_id).update({ "status": status })
        self.db.commit()


def get_file_repository(db: DatabaseDep) -> FileRepository:
    return FileRepository(db)
