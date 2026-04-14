from pydantic import BaseModel

class MessageResponse(BaseModel):
    message: str

class SearchResponse(BaseModel):
    answer: str