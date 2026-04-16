from typing import TypedDict, List, Optional

from qdrant_client.http.models import ScoredPoint

class AgentState(TypedDict):
    """State for graph"""

    query: str
    retrieved_docs: Optional[List[ScoredPoint]]

    answer: str
