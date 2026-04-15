from src.utils.extractors.base import ContentExtractor
from src.utils.extractors.docling_extractor import DoclingExtractor
from src.utils.extractors.odl_extractor import ODLExtractor

_EXTRACTOR_MAP: dict[str, type[ContentExtractor]] = {
    "pdf": ODLExtractor,
    "md": DoclingExtractor,
    "txt": DoclingExtractor,
    "csv": DoclingExtractor,
}

def get_extractor(filename: str) -> ContentExtractor:
    ext = filename.rsplit(".", 1)[-1].lower()
    extractor_class = _EXTRACTOR_MAP.get(ext, DoclingExtractor)
    return extractor_class()
