import dataclasses
from typing import Dict, Any

from langchain_text_splitters import RecursiveCharacterTextSplitter
import re
import hashlib

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_MIN_CHUNK_SIZE = 100
DEFAULT_CONTENT_TYPE = "markdown"

# This represents a processed (preprocessed and postprocessed) chunk with metadata
@dataclasses.dataclass
class Chunk:
    content: str
    metadata: Dict[str, Any]
    chunk_id: str
    start_index: int
    end_index: int

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
        cleaned_text = self.preprocess(text)

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

            chunk_id = _generate_chunk_id(doc.page_content, i)

            start_index = doc.metadata.get("start_index", 0)
            end_index = start_index + len(doc.page_content)

            metadata = {
                **source_metadata,
                "chunk_index": i,
                "chunk_size": len(doc.page_content),
                "total_chunks": len(raw_chunks),
                "preview": doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content,
            }

            chunk = Chunk(
                content=doc.page_content,
                metadata=metadata,
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


def preprocess(text: str) -> str:
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

def _generate_chunk_id(content: str, index: int) -> str:
    hash_content = f"{content[:100]}_{index}"
    return hashlib.md5(hash_content.encode()).hexdigest()[:12]