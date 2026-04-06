# src/speed_benchmark/parsers/markitdown.py
from markitdown import MarkItDown
from .base import BaseParser


class MarkItDownParser(BaseParser):
    name = "markitdown"

    def parse(self, path: str) -> str:
        md = MarkItDown()
        result = md.convert(path)
        return result.text_content
