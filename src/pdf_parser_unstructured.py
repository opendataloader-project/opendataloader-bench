import os

from unstructured.partition.pdf import partition_pdf


def to_markdown(doc_paths, input_path, output_dir):
    for doc_path in doc_paths:
        elements = partition_pdf(filename=str(doc_path), languages=["kor", "eng"])
        markdown_parts = []
        for element in elements:
            category = getattr(element, "category", None)
            text = str(element)
            if category == "Title":
                markdown_parts.append(f"# {text}")
            elif category == "Header":
                markdown_parts.append(f"## {text}")
            elif category == "Table":
                markdown_parts.append(text)
            elif category == "ListItem":
                markdown_parts.append(f"- {text}")
            else:
                markdown_parts.append(text)
        markdown = "\n\n".join(markdown_parts)
        base_name = os.path.splitext(os.path.basename(doc_path))[0]
        output_file = os.path.join(output_dir, f"{base_name}.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)
