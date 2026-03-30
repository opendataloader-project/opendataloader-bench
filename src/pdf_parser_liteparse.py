import os
import subprocess


def to_markdown(doc_paths, _, output_dir):
    for doc_path in doc_paths:
        result = subprocess.run(
            ["lit", "parse", str(doc_path), "--format", "text", "--no-ocr", "-q"],
            capture_output=True,
            text=True,
            check=True,
        )
        markdown = result.stdout

        base_name = os.path.splitext(os.path.basename(doc_path))[0]
        output_file = os.path.join(output_dir, f"{base_name}.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)
