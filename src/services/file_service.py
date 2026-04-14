import os
import ollama
import uuid
import opendataloader_pdf
import logging

from pydantic import BaseModel, Field
from typing import Any, List, Annotated
from fastapi import UploadFile, Depends
from qdrant_client.http.models import VectorParams, Distance, PointStruct

from src.dependencies import get_database_session
from src.models.file import File
from src.schemas.file import FileRead, FileBase, FileStatusEnum
from src.exceptions.exceptions import NotFoundException, BaseAppException
from src.config import get_settings
from src.utils.docling import extract_content
from src.utils.chunker import ChunkingPipeline, Chunk
from src.vector_database.qdrant import client
from src.repositories.file_repository import FileRepository

DEFAULT_START_SKIP: int = 0
DEFAULT_FILE_LIMIT: int = 100

PIPELINE_CHUNK_SIZE: int = 1500
PIPELINE_CHUNK_OVERLAP_SIZE: int = 200
PIPELINE_MIN_CHUNK_SIZE: int = 100
PIPELINE_DOC_TYPE: str = "markdown"

settings = get_settings()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FormatedLLMOutput(BaseModel):
    answer: float = Field(
        description="The message that answers the users question or 'I don't know'",
    )

async def get_file_by_id(file_id: int, repo: FileRepository) -> File:
    file = await repo.get_by_id(file_id)
    if not  file:
        raise NotFoundException(f"File with id {file_id} not found!")
    return file

async def get_files_filtered(status: FileStatusEnum, skip: int, limit: int, repo: FileRepository) -> List[File]:
    return await repo.get_filtered_files(status, skip, limit)

# This function should only handle the file upload / the file creation in the database
async def upload_file(
        uploaded_file: UploadFile,
        repo: FileRepository,
) -> FileBase:
    # Create upload dir when needed
    os.makedirs(settings.UPLOAD_DESTINATION, exist_ok=True)

    # Define file path
    file_path = os.path.join(str(settings.UPLOAD_DESTINATION), str(uploaded_file.filename))

    # Write uploaded file to destination
    with open(file_path, "wb") as f:
        content = await uploaded_file.read()
        f.write(content)

    # Create a FileCreate instance from the uploaded file using the mapper
    file_create = FileBase(filename=str(uploaded_file.filename), status=FileStatusEnum.READY, path=file_path)

    # close the stream
    await uploaded_file.close()

    created_file = await repo.create(**file_create.model_dump())

    await repo.session.commit()

    return file_create

async def process_files_by_ids(file_ids: List[int], repo: FileRepository) -> list[File]:
    files = []

    for file_id in file_ids:
        file = await process_file_by_id(file_id, repo)
        files.append(file)

    return files

# Find file path in database, read raw file, start content extraction, create chunks, generate embeddings
async def process_file_by_id(file_id: int, repo: FileRepository):
    file = await repo.get_by_id(file_id)

    if file is None:
        raise NotFoundException(f"File with id {file_id} not found!")

    file_extension = file.filename.split(".")[-1].lower()
    file_path = file.path

    # Read the files content
    try:
        with open(file_path, "rb") as f:
            raw_file_content = f.read()
    except OSError:
        raise BaseAppException("Failed to read file!")

    # Throw an error for not yet supported file types
    if file_extension == "txt" or file_extension == "md":
        raise BaseAppException(f"File type {file_extension} is not supported yet")

    # Content Extraction with Docling
    try:
        file_content = extract_content(raw_file_content, file_path)
    except Exception as exc:
        raise BaseAppException(f"Failed to extract file content using docling: {exc}")

    # Using OpenDataLoader
    try:
        opendataloader_pdf.convert(
            input_path=[f'{file_path}'],
            output_dir="uploads",
            format="json,html",
        )
    except Exception as exc:
        raise BaseAppException(f"Failed to convert file using OpenDataLoader: {exc}")

    # Write extracted content
    try:
        with open(file_path + ".md", "w") as f:
            f.write(file_content)
    except Exception as exc:
        raise BaseAppException(f"Failed to write extracted content: {exc}")

    chunking_pipeline = ChunkingPipeline(
        chunk_size=PIPELINE_CHUNK_SIZE,
        chunk_overlap=PIPELINE_CHUNK_OVERLAP_SIZE,
        min_chunk_size=PIPELINE_MIN_CHUNK_SIZE,
        document_type=PIPELINE_DOC_TYPE
    )

    generated_chunks = chunking_pipeline.chunk(text=file_content,
        source_metadata={"source": file_path + ".md"})

    logging.info(f"Generated {len(generated_chunks)} chunks\n")

    # Generate Embeddings using ollama
    generate_embeddings(file.filename, generated_chunks)

    await repo.update_status(file.id, FileStatusEnum.COMPLETED)
    await repo.session.commit()

def generate_embeddings(filename: str, chunks: List[Chunk]):
    print("Generating embeddings...")

    embeddings = ollama.embed(
        model="nomic-embed-text:latest",
        input=[chunk.content for chunk in chunks],
    )

    embedding_length = len(embeddings['embeddings'][0])

    # Currently the qdrant collection is recreated every time. Not optimal
    client.recreate_collection(
        collection_name="files",
        vectors_config=VectorParams(
            size=embedding_length,
            distance=Distance.COSINE
        ),
    )

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

    client.upsert(collection_name="files", points=points)

def search(query: str) -> str:
    query_embedding = ollama.embed(
        model="nomic-embed-text:latest",
        input=query,
    )['embeddings'][0]

    results = client.query_points(
        collection_name="files",
        query=query_embedding,
        with_payload=True,
        limit=5,
        score_threshold=0.5,
    ).points

    print(f"found {len(results)} documents\n")

    prompt_sources = "\n\n".join([hit.payload.get('text')['content'] for hit in results])

    SYSTEM_PROMPT = f"""
        You are a helpful assistant.
        Answer the following question only based on the following sources below.
        If the answer is not in the sources, say "I don't know". If the question has nothing to do with the provided sources, say "I don't know".
        Do not use any external knowledge, assumptions, or general LLM knowledge, only the context provided should be used.
    """

    HUMAN_PROMPT = f"""
    User question:
    {query}

    Context Documents: {prompt_sources}

    Provide the reasoning behind.
    """

    response = ollama.chat(model="llama3.1", messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": HUMAN_PROMPT},
    ])

    print(response)

    # answer = FormatedLLMOutput.model_validate_json(response.message.content)
    #
    # print(answer)

    return response['message']['content']