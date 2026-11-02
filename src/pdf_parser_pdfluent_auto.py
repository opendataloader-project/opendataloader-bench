"""PDF parser using PDFluent (https://pdfluent.com), public Python API only.

Engine "pdfluent-auto": quality="auto". Layout and table models for born-digital
pages, OCR for pages without a text layer. The models are installed with

    python -m pdfluent models install layout tables

Without them the library falls back to the fast tier with a warning, so the
models are checked up front and the run fails instead. The optional `formula`
model may be missing. Page headers and footers are kept (keep_furniture=True)
because this benchmark's ground truth counts them as content; PDFluent drops
them by default.
"""

import os
import subprocess
import sys

import pdfluent


def _models_ready() -> None:
    """Fail unless `pdfluent models status` reports every required file as verified."""
    out = subprocess.run(
        [sys.executable, "-m", "pdfluent", "models", "status"], capture_output=True, text=True
    )
    lines = [line for line in out.stdout.splitlines() if line.strip()]
    optional_formula_missing = lambda line: line.startswith("formula ") and line.endswith(": missing")
    if out.returncode != 0 or not lines or not all("sha256 ok" in line or optional_formula_missing(line) for line in lines):
        raise RuntimeError("PDFluent models are not installed or do not verify:\n" + out.stdout + out.stderr)


def to_markdown(doc_paths, input_path, output_dir):
    _models_ready()
    for doc_path in doc_paths:
        base_name = os.path.splitext(os.path.basename(doc_path))[0]
        markdown = pdfluent.open(str(doc_path)).extract_markdown(quality="auto", keep_furniture=True)
        with open(os.path.join(output_dir, f"{base_name}.md"), "w", encoding="utf-8") as f:
            f.write(markdown)
