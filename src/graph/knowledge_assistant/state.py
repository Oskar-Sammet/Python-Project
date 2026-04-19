from typing import TypedDict, List, Optional, Annotated

from langgraph.graph.message import add_messages
from qdrant_client.http.models import ScoredPoint

class AgentState(TypedDict):
    """State for graph"""

    query: str
    retrieved_docs: Optional[List[ScoredPoint]]
    answer: str
    messages: Annotated[list, add_messages]
