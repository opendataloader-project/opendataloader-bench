import os
import shutil
import subprocess


def to_markdown(doc_paths, input_path, output_dir):
    pdf_to_md_bin = shutil.which("pdf-to-markdown")

    for doc_path in doc_paths:
        base_name = os.path.splitext(os.path.basename(doc_path))[0]
        output_file = os.path.join(output_dir, f"{base_name}.md")

        if pdf_to_md_bin:
            subprocess.run(
                [pdf_to_md_bin, str(doc_path), output_file],
                check=True,
            )
        else:
            subprocess.run(
                ["npx", "@pspdfkit/pdf-to-markdown", str(doc_path), output_file],
                check=True,
            )
