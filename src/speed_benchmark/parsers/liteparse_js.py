# src/speed_benchmark/parsers/liteparse_js.py
import shutil
import subprocess
from pathlib import Path
from .base import BaseParser

# parsers/ -> speed_benchmark/ -> src/ -> project-root/
_RUNNER = Path(__file__).parent.parent / "liteparse_runner.js"


class LiteParseJsParser(BaseParser):
    name = "liteparse-js"

    def is_available(self) -> bool:
        return shutil.which("node") is not None and _RUNNER.exists()

    def parse(self, path: str) -> str:
        result = subprocess.run(
            ["node", str(_RUNNER), path],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
