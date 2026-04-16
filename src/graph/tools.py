import json

from langchain.tools import tool
from src.vector_database.qdrant import client


@tool
def get_document_neighbors(document_id: str) -> str:
    """Fetch the previous and next chunks for a document that appears cut off."""
    records = client.retrieve(collection_name="files", ids=[document_id], with_payload=True)

    if not records:
        return json.dumps([])

    point = records[0]

    neighbour_ids = []
    if point.payload.get("prev_id"):
        neighbour_ids.append(point.payload["prev_id"])
    if point.payload.get("next_id"):
        neighbour_ids.append(point.payload["next_id"])

    if not neighbour_ids:
        return json.dumps([])

    neighbours = client.retrieve(collection_name="files", ids=neighbour_ids, with_payload=True)
    return json.dumps([{"id": str(r.id), "payload": r.payload} for r in neighbours])


tools = [get_document_neighbors]
