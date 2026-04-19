from abc import ABC, abstractmethod
from src.utils.chunker import Chunk

class ContentExtractor(ABC):

    @abstractmethod
    def extract(self, raw_content: bytes, file_path: str) -> list[Chunk]:
       ...