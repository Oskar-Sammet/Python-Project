import json
import logging

import opendataloader_pdf as odl_pdf

from src.app.exceptions.exceptions import BaseAppException
from src.utils.chunker import Chunk, odl_chunking
from src.utils.extractors.base import ContentExtractor

logger = logging.getLogger(__name__)

class ODLExtractor(ContentExtractor):
    def __init__(self, output_dir: str = "uploads"):
        self.output_dir = output_dir

    def extract(self, raw_content: bytes, file_path: str) -> list[Chunk]:
        filename_without_ext = ".".join(file_path.rsplit("/", 1)[-1].split(".")[:-1])

        try:
            odl_pdf.convert(
                input_path=[file_path],
                output_dir=self.output_dir,
                format="json",
            )
            with open(f"{self.output_dir}/{filename_without_ext}.json", encoding="utf-8") as f:
                doc = json.load(f)
        except Exception as exc:
            raise BaseAppException(f"Failed to convert file using OpenDataLoader: {exc}")

        return odl_chunking(doc)
