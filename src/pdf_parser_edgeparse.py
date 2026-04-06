import os
import shutil
import subprocess


def to_markdown(doc_paths, input_path, output_dir):
    edgeparse_bin = shutil.which("edgeparse")

    for doc_path in doc_paths:
        base_name = os.path.splitext(os.path.basename(doc_path))[0]
        output_file = os.path.join(output_dir, f"{base_name}.md")

        if edgeparse_bin:
            subprocess.run(
                [edgeparse_bin, "parse", "--format", "markdown", str(doc_path), "-o", output_file],
                check=True,
            )
        else:
            from edgeparse import parse

            markdown = parse(str(doc_path), format="markdown")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(markdown)
