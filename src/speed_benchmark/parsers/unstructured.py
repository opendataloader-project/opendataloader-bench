# src/speed_benchmark/parsers/unstructured.py
from .base import BaseParser


class UnstructuredParser(BaseParser):
    name = "unstructured"

    def parse(self, path: str) -> str:
        from unstructured.partition.pdf import partition_pdf
        elements = partition_pdf(filename=path)
        return "\n\n".join(str(e) for e in elements)

    def is_available(self) -> bool:
        try:
            from unstructured.partition.pdf import partition_pdf
            return True
        except ImportError:
            return False
