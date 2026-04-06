# src/speed_benchmark/parsers/pymupdf.py
import pymupdf
from .base import BaseParser


class PyMuPDFParser(BaseParser):
    name = "pymupdf"

    def parse(self, path: str) -> str:
        doc = pymupdf.open(path)
        return "\n".join(page.get_text() for page in doc)
