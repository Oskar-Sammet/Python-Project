import logging

from docling.exceptions import ConversionError

from src.app.exceptions.exceptions import BaseAppException
from src.utils.docling import extract_content
from src.utils.chunker import Chunk, ChunkingPipeline
from src.utils.extractors.base import ContentExtractor

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200
MIN_CHUNK_SIZE = 100
DOCUMENT_TYPE = "markdown"

class DoclingExtractor(ContentExtractor):
    def extract(self, raw_content: bytes, file_path: str) -> list[Chunk]:
        try:
            file_content = extract_content(raw_content, file_path)
        except ConversionError:
            logger.error("Docling ConversionError: File format not allowed, falling back to UTF-8 decode")
            try:
                file_content = raw_content.decode("utf-8")
            except UnicodeDecodeError:
                raise BaseAppException("Failed to decode file! File content type not supported!")

        try:
            with open(file_path + ".md", "w") as f:
                f.write(file_content)
        except Exception as exc:
            raise BaseAppException(f"Failed to write extracted content: {exc}")

        pipeline = ChunkingPipeline(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            min_chunk_size=MIN_CHUNK_SIZE,
            document_type=DOCUMENT_TYPE,
        )

        return pipeline.chunk(text=file_content, source_metadata={
            "source": "",
            "file_name": file_path + ".md",
            "file_type": "",
        })
