# src/speed_benchmark/parsers/opendataloader.py
import tempfile
from pathlib import Path

from opendataloader_pdf import convert

from .base import BaseParser


class OpenDataLoaderParser(BaseParser):
    name = "opendataloader-pdf"

    def parse(self, path: str) -> str:
        with tempfile.TemporaryDirectory() as tmpdir:
            convert(path, output_dir=tmpdir, format="text", quiet=True)
            output_files = list(Path(tmpdir).glob("*.txt"))
            if not output_files:
                return ""
            return output_files[0].read_text()
