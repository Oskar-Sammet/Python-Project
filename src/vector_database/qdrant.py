from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from src.config import get_settings

settings = get_settings()

client = QdrantClient(
    host=settings.QDRANT_HOST,
    port=settings.QDRANT_PORT
)

def create_collection(collection_name: str, size: int = 100):
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=size, distance=Distance.COSINE),
        )