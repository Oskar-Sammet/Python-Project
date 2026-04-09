from typing import List, Annotated, Any
from fastapi import UploadFile
from qdrant_client.http.models import VectorParams, Distance, PointStruct
from sqlalchemy.orm import Session
from src.config import settings
from src.exceptions.exceptions import FileNotFoundException, BaseAppException
from src.schemas.file import FileStatusEnum, FileRead, FileCreate
from src.models.file import File
from src.utils.docling import extract_content
from src.utils.chunker import ChunkingPipeline, Chunk
from src.vector_database.qdrant import client
import os
import ollama
import uuid

def get_file(file_id: int, db: Session) -> FileRead:
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise FileNotFoundException(f"File with id {file_id} not found")
    return FileRead(**file.__dict__)

def get_files(status: FileStatusEnum | None, skip: int = 0, limit: int = 100, db: Session = None) -> list[Any]:
    query = db.query(File)

    if status is not None:
        query = query.filter(File.status == str(status.value))

    return query.offset(skip).limit(limit).all()

# This function should only handle the file upload / the file creation in the database
async def upload_file(uploaded_file: Annotated[UploadFile, File()], db: Session):
    # Validate the files extension and content type
    # await upload_validator.validate(data)

    # Create upload dir when needed
    os.makedirs(settings.UPLOAD_DESTINATION, exist_ok=True)

    # Define file path
    file_path = os.path.join(settings.UPLOAD_DESTINATION, uploaded_file.filename)

    # Write uploaded file to destination
    with open(file_path, "wb") as f:
        content = await uploaded_file.read()
        f.write(content)

    # Create a FileCreate instance from the uploaded file using the mapper
    file_create = FileCreate(filename=uploaded_file.filename, status=FileStatusEnum.READY, path=file_path)

    await uploaded_file.close()

    # create a file instance
    file_instance = File(**file_create.model_dump())

    if not file_instance:
        raise BaseAppException("Failed to create file instance")

    # add the file_instance to the database
    db.add(file_instance)
    db.commit()
    db.refresh(file_instance)

    return file_instance

def process_files(file_ids: List[int], db: Session):
    for file_id in file_ids:
        process_file(file_id, db)

def process_file(file_id: int, db: Session):
    # find file by id to process
    file = db.query(File).filter(File.id == file_id).first()

    if not file:
        raise FileNotFoundException("File not found")

    extension = file.filename.split(".")[-1].lower()

    # grap files content
    try:
        with open(file.path, "rb") as f:
            raw = f.read()
    except OSError:
        raise FileNotFoundException(f"File not found on disk: {file.path}")

    # Throw an error for not supported file types
    if extension == "txt" or extension == "md":
        raise BaseAppException(f"File type {extension} is not supported yet")

    try:
        content = extract_content(raw, file.filename)
    except Exception as e:
        raise BaseAppException(f"Failed to extract content from {file.filename}: {e}")

    with open(file.path + ".md", "w") as f:
        f.write(content)

    chunk_pipeline = ChunkingPipeline(
        chunk_size=1500,
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

    generate_embeddings(filename=file.path, chunks=chunks)
    # set the file status to "completed"
    db.query(File).filter(File.id == file_id).update({"status": FileStatusEnum.COMPLETED})
    db.commit()
    db.refresh(file)

    return file

def generate_embeddings(filename: str, chunks: List[Chunk]):
    print("Generating embeddings...")

    embeddings = ollama.embed(
        model="nomic-embed-text:latest",
        input=[chunk.content for chunk in chunks],
    )

    embedding_length = len(embeddings['embeddings'][0])
    client.recreate_collection(
        collection_name="files",
        vectors_config=VectorParams(
            size=embedding_length,
            distance=Distance.COSINE
        ),
    )
    # Check if collection doesn't exists already
    # if not client.collection_exists("files"):

    vectors = embeddings['embeddings']

    points = []

    for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "text": chunk,
                "filename": filename,
                "chunk_index": idx,
                "token_count": len(chunk.content.split()),
                "page": chunk.metadata.get("page", 0),
                "type": chunk.metadata.get("type", 0),
            }
        ))

    client.upsert(
        collection_name="files",
        points=points
    )

def search(query: str, db: Session):
    query_embedding = ollama.embed(
        model="nomic-embed-text:latest",
        input=query,
    )['embeddings'][0]

    results = client.query_points(
        collection_name="files",
        query=query_embedding,
        with_payload=True,
        limit=5,
        score_threshold=0.6,
    ).points

    prompt_sources = "\n\n".join([hit.payload.get('text')['content'] for hit in results])

    prompt = f"""
    You are a helpful assistant.
    Answer the following question only based on the following sources below.
    If the answer is not in the sources, say "I don't know".
    
    Context:
    {prompt_sources}
    
    Question: 
    {query}
    
    Answer:
    """

    response = ollama.chat(model="llama3.1", messages=[
        {"role": "user", "content": prompt}
    ])

    return response['message']['content']