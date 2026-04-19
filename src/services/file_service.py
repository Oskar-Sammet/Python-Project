import ollama
import uuid
import logging

from pydantic import BaseModel, Field
from typing import List
from fastapi import UploadFile
from qdrant_client.http.models import VectorParams, Distance, PointStruct, ScoredPoint

from src.graph.knowledge_assistant.graph import AgentState, graph
from src.models.file import File
from src.schemas.file import FileBase, FileStatusEnum
from src.app.exceptions.exceptions import NotFoundException, BaseAppException
from src.config import get_settings
from src.utils.extractors import get_extractor
from src.vector_database.qdrant import client
from src.repositories.file_repository import FileRepository
from utils.chunker import Chunk

DEFAULT_START_SKIP: int = 0
DEFAULT_FILE_LIMIT: int = 100

settings = get_settings()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FormatedLLMOutput(BaseModel):
    answer: float = Field(
        description="The message that answers the users question or 'I don't know'",
    )

async def get_file_by_id(file_id: int, repo: FileRepository) -> File:
    file = await repo.get_by_id(file_id)
    if not file:
        raise NotFoundException(f"File with id {file_id} not found!")
    return file

async def get_files_filtered(status: FileStatusEnum, skip: int, limit: int, repo: FileRepository) -> List[File]:
    return await repo.get_filtered_files(status, skip, limit)

# This function should only handle the file process / the file creation in the database
async def upload_file(uploaded_file: UploadFile, repo: FileRepository):
    await process_graph.ainvoke(ProcessState(
        uploaded_file=uploaded_file,
        repo=repo,

        file_name="",
        upload_dir="",
        full_path="",
    ))

async def process_files_by_ids(file_ids: List[int], repo: FileRepository) -> list[File]:
    files = []

    for file_id in file_ids:
        file = await process_file_by_id(file_id, repo)
        files.append(file)

    return files

# Find file path in database, extract content, create chunks, generate embeddings
async def process_file_by_id(file_id: int, repo: FileRepository):
    file = await repo.get_by_id(file_id)

    if file is None:
        raise NotFoundException(f"File with id {file_id} not found!")

    try:
        with open(file.path, "rb") as f:
            raw_file_content = f.read()
    except OSError:
        raise BaseAppException("Failed to read file!")

    extractor = get_extractor(file.filename)
    chunks = extractor.extract(raw_file_content, file.path)

    logger.info(f"Generated {len(chunks)} chunks using {type(extractor).__name__}")

    generate_embeddings(file.filename, chunks)

    await repo.update_status(file.id, FileStatusEnum.COMPLETED)
    await repo.session.commit()

def generate_embeddings(filename: str, chunks: List[Chunk]):
    logger.info(f"Generating embeddings for {len(chunks)} chunks\n")

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
    point_ids = [str(uuid.uuid4()) for _ in range(len(vectors))]
    points = []

    for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
        prev_id = point_ids[idx - 1] if idx > 0 else None
        next_id = point_ids[idx + 1] if idx < len(chunks) - 1 else None

        # payload
        points.append(PointStruct(
            id=point_ids[idx],
            vector=vector,
            payload={
                "id": chunk.chunk_id,
                "content": chunk.content,

                "metadata": chunk.metadata,

                "relations": {
                    "prev_id": prev_id,
                    "next_id": next_id,
                },

                "offsets": {
                    "start": chunk.start_index,
                    "end": chunk.end_index
                },
            }
        ))

    client.upsert(collection_name="files", points=points)

def retrieve_points(query: str) -> list[ScoredPoint]:
    query_embedding = ollama.embed(
        model=settings.OLLAMA_EMBEDDING_MODEL,
        input=query,
    )['embeddings'][0]

    queried_points = client.query_points(
        collection_name="files",
        query=query_embedding,
        with_payload=True,
        limit=5,
        score_threshold=0.5,
    ).points

    existing_ids = {point.id for point in queried_points}
    neighbor_ids = set()

    for point in queried_points:
        if point.payload['relations']['prev_id']:
            neighbor_ids.add(point.payload['relations']['prev_id'])
        if point.payload['relations']['next_id']:
            neighbor_ids.add(point.payload['relations']['next_id'])

    new_ids = list(neighbor_ids - existing_ids)

    if new_ids:
        neighbors = client.retrieve(
            collection_name="files",
            ids=new_ids,
            with_payload=True,
        )
        queried_points.extend(
            ScoredPoint(id=r.id, payload=r.payload, score=0.0, version=0)
            for r in neighbors
        )

    return queried_points

def search(query: str) -> dict:
    state = graph.invoke(AgentState(query=query, answer="", retrieved_docs=None))
    return state