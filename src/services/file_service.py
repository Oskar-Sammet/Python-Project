from sqlalchemy.orm import Session

from src.exceptions.exceptions import FileNotFoundException
from src.schemas.file import FileStatusEnum
from src.schemas.file import FileCreate
from src.models.file import File
from src.utils.docling import extract_content

def get_file(id: str, db: Session) -> type[File] | None:
    return db.query(File).filter(File.id == id).first()

def get_files(skip: int = 0, limit: int = 100, db: Session = None):
    return db.query(File).filter(File.status == FileStatusEnum.completed).offset(skip).limit(limit).all()

# This function should only handle the file upload / the file creation in the database
def upload_file(data: FileCreate, db: Session):
    # create a file instance
    file_instance = File(**data.model_dump())

    # add the file_instance to the database
    db.add(file_instance)
    db.commit()
    db.refresh(file_instance)

    return file_instance

def process_file(file_id: int, db: Session):
    # find file by id to process
    file = db.query(File).filter(File.id == file_id).first()

    if not file:
        raise FileNotFoundException("File not found")

    # grap files content
    with open(file.path, "rb") as f:
        raw = f.read()

    if file.filename.lower().endswith(".txt"):
        content = raw.decode("utf-8")
    else:
        content = extract_content(raw, file.filename)

    with open(file.path + ".md", "w") as f:
        f.write(content)

    # set the file status to "completed"
    db.query(File).filter(File.id == file_id).update({"status": FileStatusEnum.completed})
    db.commit()
    db.refresh(file)

    return file