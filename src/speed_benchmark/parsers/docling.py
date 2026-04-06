# src/speed_benchmark/parsers/docling.py
from .base import BaseParser


class DoclingParser(BaseParser):
    name = "docling"

    def parse(self, path: str) -> str:
        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()
        result = converter.convert(path)
        return result.document.export_to_markdown()

    def is_available(self) -> bool:
        try:
            from docling.document_converter import DocumentConverter
            return True
        except ImportError:
            return False
