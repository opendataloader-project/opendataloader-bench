# src/speed_benchmark/parsers/edgeparse.py
import shutil
import subprocess
from .base import BaseParser


class EdgeParseParser(BaseParser):
    name = "edgeparse"

    def parse(self, path: str) -> str:
        result = subprocess.run(
            ["edgeparse", "parse", "--format", "markdown", path],
            capture_output=True, text=True, check=True,
        )
        return result.stdout

    def is_available(self) -> bool:
        return shutil.which("edgeparse") is not None
