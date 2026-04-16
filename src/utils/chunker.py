import dataclasses
from typing import Dict, Any, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter
import re
import hashlib
import json

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_MIN_CHUNK_SIZE = 100
DEFAULT_CONTENT_TYPE = "markdown"

# This represents a processed (preprocessed and postprocessed) chunk with metadata
@dataclasses.dataclass
class Chunk:
    content: str
    metadata: Optional[ChunkMetadata]
    chunk_id: str
    start_index: int
    end_index: int

@dataclasses.dataclass
class ChunkMetadata:
    source_id: SourceMetadata
    page_number: int
    chunk_index: int
    total_chunks: int
    #token_count: int

@dataclasses.dataclass
class SourceMetadata:
    source: Optional[str]
    file_name: Optional[str]
    file_type: Optional[str]

class ChunkingPipeline:
    def __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE, chunk_overlap: int = DEFAULT_CHUNK_OVERLAP, min_chunk_size: int = DEFAULT_MIN_CHUNK_SIZE, document_type: str = DEFAULT_CONTENT_TYPE):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

        self.separators = _get_separators(document_type)

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=self.separators,
            length_function=len,
            add_start_index=True,
        )

    def chunk(self, text: str, source_metadata: Dict[str, Any] = None):
        if source_metadata is None:
            source_metadata = {}

        # Preprocess the text before splitting it into chunks
        cleaned_text = _preprocess(text)

        # Chunking
        raw_chunks = self.splitter.create_documents(
            texts=[cleaned_text],
            metadatas=[source_metadata]
        )

        # Postprocessing
        processed_chunks = []

        for i, doc in enumerate(raw_chunks):
            # Skip too small chunks
            if len(doc.page_content) < self.min_chunk_size:
                continue

            chunk_id = generate_chunk_id(doc.page_content, i)

            start_index = doc.metadata.get("start_index", 0)
            end_index = start_index + len(doc.page_content)

            # text.metadata
            metadata = {
                "source_id": source_metadata,

                "page_number": 0,
                "chunk_index": i,
                "total_chunks": len(doc.page_content),
            }

            # text
            chunk = Chunk(
                content=doc.page_content,
                metadata=ChunkMetadata(**metadata),
                chunk_id=chunk_id,
                start_index=start_index,
                end_index=end_index,
            )

            processed_chunks.append(chunk)

        return processed_chunks

    def merge_small_chunks(self, chunks: list[Chunk]) -> list[Chunk]:
        if not chunks:
            return chunks

        merged_chunks = []
        current_chunk = chunks[0]

        for next_chunk in chunks[1:]:
            combined_size = len(current_chunk.content) + len(next_chunk.content)

            if combined_size <= self.chunk_size:
                current_chunk = Chunk(
                    content=current_chunk.content + next_chunk.content,
                    metadata=current_chunk.metadata,
                    chunk_id=current_chunk.chunk_id,
                    start_index=current_chunk.start_index,
                    end_index=next_chunk.end_index,
                )
            else:
                merged_chunks.append(current_chunk)
                current_chunk = next_chunk

        merged_chunks.append(current_chunk)
        return merged_chunks

def _get_separators(document_type: str) -> list[str]:
    separator_map = {
        "pdf": ["\n\n", "\n", ".", " ", ""],
        "txt": ["\n"],
        "markdown": ["## ", "### ", "#### ", "\n\n", "\n", ". ", " ", ""],
    }

    return separator_map.get(document_type, separator_map["markdown"])

def _preprocess(text: str) -> str:
    text = text.encode("utf-8", errors="ignore").decode("utf-8")

    # Standardize the line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove excessive spaces
    text = re.sub(r" {2,}", " ", text)

    # Strip leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()

def generate_chunk_id(content: str, index: int) -> str:
    hash_content = f"{content[:100]}_{index}"
    return hashlib.md5(hash_content.encode()).hexdigest()[:12]

def odl_chunking(doc, min_chars=200):
    """Best for: Balanced chunk sizes, reducing noise."""
    chunks = []
    buffer_text = ""
    buffer_pages = []

    for element in doc["kids"]:
        if element["type"] in ("paragraph", "heading", "list"):
            buffer_text += element.get("content", "") + "\n"
            page = element.get("page number")
            if page and page not in buffer_pages:
                buffer_pages.append(page)

            if len(buffer_text) >= min_chars:
                content = buffer_text.strip()
                chunks.append(Chunk(
                    chunk_id=generate_chunk_id(content, element.get('id')),
                    content=content,
                    metadata={
                        "type": element["type"],
                        "pages": buffer_pages.copy(),
                        "bbox": element.get("bounding box"),
                        "source": doc.get("file name"),
                    },
                    start_index = 0,
                    end_index=0,
                ))
                buffer_text = ""
                buffer_pages = []

    if buffer_text.strip():
        chunks.append({"text": buffer_text.strip(), "metadata": {"pages": buffer_pages}})

    return chunks