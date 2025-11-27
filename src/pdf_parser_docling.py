import os
from docling.document_converter import DocumentConverter


def to_markdown(doc_paths, _, output_dir):
    converter = DocumentConverter()
    for doc_path in doc_paths:
        result = converter.convert(doc_path)
        markdown = result.document.export_to_markdown()

        base_name = os.path.splitext(os.path.basename(doc_path))[0]
        output_file = os.path.join(output_dir, f"{base_name}.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)
