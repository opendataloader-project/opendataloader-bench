"""PDF parser using PDFluent (https://pdfluent.com), public Python API only.

Engine "pdfluent-fast": quality="fast", pure Rust, no models. Page headers and
footers are kept (keep_furniture=True) because this benchmark's ground truth
counts them as content; PDFluent drops them by default.
"""

import os

import pdfluent


def to_markdown(doc_paths, input_path, output_dir):
    for doc_path in doc_paths:
        base_name = os.path.splitext(os.path.basename(doc_path))[0]
        try:
            markdown = pdfluent.open(str(doc_path)).extract_markdown(quality="fast", keep_furniture=True)
        except Exception as exc:
            print(f"FAILED {base_name}: {exc}")
            markdown = ""
        with open(os.path.join(output_dir, f"{base_name}.md"), "w", encoding="utf-8") as f:
            f.write(markdown)
