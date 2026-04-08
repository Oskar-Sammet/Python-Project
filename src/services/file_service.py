from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session

from src.exceptions.exceptions import FileNotFoundException
from src.schemas.file import FileStatusEnum
from src.schemas.file import FileCreate
from src.models.file import File
from src.utils.docling import extract_content
from src.utils.chunker import ChunkingPipeline

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

    extension = file.filename.split(".")[-1].lower()

    # grap files content
    with open(file.path, "rb") as f:
        raw = f.read()

    if extension == "txt":
        content = raw.decode("utf-8")
    else:
        content = extract_content(raw, file.filename)

    with open(file.path + ".md", "w") as f:
        f.write(content)

    chunk_pipeline = ChunkingPipeline(
        chunk_size=500,
        chunk_overlap=100,
        min_chunk_size=50,
        document_type="markdown"
    )

    chunks = chunk_pipeline.chunk(
        text=content, source_metadata={
            "source": file.path + ".md",
        })

    print(f"Generated {len(chunks)} chunks\n")

    for chunk in chunks:
        print(f"ID: {chunk.chunk_id}")
        print(f"Size: {chunk.metadata['chunk_size']} chars")
        print(f"Preview: {chunk.metadata['preview']}")
        print("-" * 50)

    # set the file status to "completed"
    db.query(File).filter(File.id == file_id).update({"status": FileStatusEnum.completed})
    db.commit()
    db.refresh(file)

    return file

