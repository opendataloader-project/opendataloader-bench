# src/speed_benchmark/parsers/nutrient.py
import shutil
import subprocess
from .base import BaseParser


class NutrientParser(BaseParser):
    name = "nutrient"

    def parse(self, path: str) -> str:
        if shutil.which("pdf-to-markdown"):
            cmd = ["pdf-to-markdown", path]
        else:
            cmd = ["npx", "@pspdfkit/pdf-to-markdown", path]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout

    def is_available(self) -> bool:
        return shutil.which("pdf-to-markdown") is not None or shutil.which("npx") is not None
