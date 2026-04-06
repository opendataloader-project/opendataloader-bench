# src/speed_benchmark/parsers/liteparse_cli.py
import shutil
import subprocess
from .base import BaseParser


class LiteParseCliParser(BaseParser):
    name = "liteparse-cli"

    def is_available(self) -> bool:
        return shutil.which("npx") is not None

    def parse(self, path: str) -> str:
        result = subprocess.run(
            ["npx", "@llamaindex/liteparse", "parse", "--no-ocr", path],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
