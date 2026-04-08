from io import BytesIO
from typing import Any

from click import prompt
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableStructureOptions, TableFormerMode, \
    PictureDescriptionApiOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import ImageRefMode
from docling_core.types.io import DocumentStream
import os

OLLAMA_URL = "http://localhost:11434"
VLM_MODEL = "qwen3.5:2b"
VLM_PROMPT = "Explain what you see in the image in 1 sentence."

PAGE_BREAK_PLACEHOLDER = "<!-- page break -->"
IMAGE_DESCRIPTION_START = "<image_description>"
IMAGE_DESCRIPTION_END = "</image_description>"

def create_picture_description_options() -> PictureDescriptionApiOptions:
    return PictureDescriptionApiOptions(
        url = f"{OLLAMA_URL}/v1/chat/completions",
        params=dict[str, Any](
            model=VLM_MODEL,
            think=False,
            seed=42,
            max_completion_tokens=256,
        ),
        prompt=VLM_PROMPT,
        timeout=90,
    )

def create_pdf_pipeline_option() -> PdfPipelineOptions:
    return PdfPipelineOptions(
        enable_remote_services=True,
        do_ocr=False,
        do_table_structure=True,
        generate_picture_images=False,
        do_picture_description=False,
        table_structure_options=TableStructureOptions(
            mode=TableFormerMode.ACCURATE
        ),
        #picture_description_options=create_picture_description_options(),
    )

def process_document(stream: DocumentStream):
    # Returns a Docling Document
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=create_pdf_pipeline_option(),
                backend=PyPdfiumDocumentBackend
            )
        }
    )

    # Returns a ConversationalResult which contains the Docling Document
    # has some extra information like the docling document version, pages, ...
    result = converter.convert(stream)

    # This gets the Docling Document from the ConversationalResult
    doc = result.document

    content = doc.export_to_markdown(
        image_mode=ImageRefMode.PLACEHOLDER,
        image_placeholder="", # ![image]({image_ref})
        page_break_placeholder=PAGE_BREAK_PLACEHOLDER,
        include_annotations=True,
        mark_annotations=True
    )

    content = content.replace(
        '<!--<annotation kind="description">-->', IMAGE_DESCRIPTION_START
    )

    content = content.replace("<!--<annotation />-->", IMAGE_DESCRIPTION_END)

    content = content.replace('-', '')
    content = content.strip()

    content = os.linesep.join([
        line for line in content.splitlines()
        if line
    ])

    return content

def extract_content(file_bytes: bytes, filename: str) -> str:
    stream = DocumentStream(name=filename, stream=BytesIO(file_bytes))
    return process_document(stream)
