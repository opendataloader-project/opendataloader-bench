import os
from markitdown import MarkItDown


def to_markdown(doc_paths, _, output_dir):
    for doc_path in doc_paths:
        result = MarkItDown().convert(doc_path)
        markdown = result.text_content

        base_name = os.path.splitext(os.path.basename(doc_path))[0]
        output_file = os.path.join(output_dir, f"{base_name}.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)
