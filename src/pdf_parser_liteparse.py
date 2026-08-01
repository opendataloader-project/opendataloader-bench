import os

from liteparse import LiteParse


def to_markdown(doc_paths, input_path, output_dir):
    # OCR only has minor increase in accuracy on this dataset, enable if you want.
    # `image_mode="off"` and `extract_links=False` keep the output plain-text so it
    # matches the ground truth, which carries no image placeholders or [text](url)
    # link syntax. `quiet=True` suppresses per-document timing logs, which otherwise
    # add measurable stdout overhead to the speed benchmark.
    lp = LiteParse(
        output_format="markdown",
        image_mode="off",
        ocr_enabled=False,
        extract_links=False,
        quiet=True,
    )

    for doc_path in doc_paths:
        result = lp.parse(str(doc_path))
        base_name = os.path.splitext(os.path.basename(doc_path))[0]
        output_file = os.path.join(output_dir, f"{base_name}.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result.text)
