"""PDF parser using Nutrient's pdf-to-markdown CLI.

Invokes the CLI in folder mode (one subprocess per directory) when given a
directory, and in single-file mode when given one PDF. Requires the
``pdf-to-markdown`` binary on PATH — install with:
``npm install -g @pspdfkit/pdf-to-markdown``.
"""

import shutil
import subprocess
from pathlib import Path

_pdf_to_md_bin = shutil.which("pdf-to-markdown")
if _pdf_to_md_bin is None:
    raise ImportError(
        "pdf-to-markdown not found on PATH. "
        "Install it with: npm install -g @pspdfkit/pdf-to-markdown"
    )


def to_markdown(doc_paths, input_path, output_dir):
    """Convert PDF(s) to Markdown via the pdf-to-markdown CLI.

    When ``input_path`` is a directory, the CLI is invoked once in folder
    mode for the whole corpus. When it is a single file, output is written
    to a named ``.md`` file inside ``output_dir``.
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)

    if input_path.is_file():
        output = output_dir / (input_path.stem + ".md")
    else:
        output = output_dir

    subprocess.run(
        [_pdf_to_md_bin, str(input_path), str(output)],
        check=True,
    )
