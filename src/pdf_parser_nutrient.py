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
