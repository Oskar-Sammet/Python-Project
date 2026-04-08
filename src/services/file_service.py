from sqlalchemy.orm import Session
from sqlalchemy import select

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
    # grap files content
    content = extract_content(file.content, file.filename)



    # clean content


    # generate embeddings using ollama
    # embeddings = ollama.embed(model="nomic-embed-text", input=content)
    # embedding_length = len(embeddings['embeddings'][0])

    # collection is only created if it doesn't exist already
    # create_collection(collection_name="files", size=embedding_length)

    # client.upsert(
    #     collection_name="files",
    #     points=[
    #         PointStruct(id=idx, vector=vector, payload={"filename": file.filename})
    #         for idx, vector in enumerate(embeddings['embeddings'])
    #     ]
    # )