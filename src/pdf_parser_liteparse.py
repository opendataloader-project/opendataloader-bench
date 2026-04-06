import os

from liteparse import LiteParse


def to_markdown(doc_paths, input_path, output_dir):
    lp = LiteParse()
    for doc_path in doc_paths:
        result = lp.parse(str(doc_path))
        base_name = os.path.splitext(os.path.basename(doc_path))[0]
        output_file = os.path.join(output_dir, f"{base_name}.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result.text)
