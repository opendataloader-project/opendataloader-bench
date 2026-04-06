# src/speed_benchmark/parsers/pypdf.py
from pypdf import PdfReader
from .base import BaseParser


class PyPDFParser(BaseParser):
    name = "pypdf"

    def parse(self, path: str) -> str:
        reader = PdfReader(path)
        return "\n".join(
            page.extract_text() or "" for page in reader.pages
        )
