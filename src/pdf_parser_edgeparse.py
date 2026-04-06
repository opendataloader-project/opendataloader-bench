import os

from edgeparse import convert


def to_markdown(doc_paths, input_path, output_dir):
    for doc_path in doc_paths:
        markdown = convert(str(doc_path), format="markdown")
        base_name = os.path.splitext(os.path.basename(doc_path))[0]
        output_file = os.path.join(output_dir, f"{base_name}.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)
