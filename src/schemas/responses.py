from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any

class ErrorResponse(BaseModel):
    """Standard error response format"""
    error: str
    code: str
    timestamp: datetime
    path: str
    details: Optional[Any] = None

class MessageResponse(BaseModel):
    message: str

class SearchResponse(BaseModel):
    answer: str