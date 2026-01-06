import os

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered


def to_markdown(doc_paths, _, output_dir):
    converter = PdfConverter(artifact_dict=create_model_dict())
    for doc_path in doc_paths:
        rendered = converter(str(doc_path))
        text, _, images = text_from_rendered(rendered)

        base_name = os.path.splitext(os.path.basename(doc_path))[0]
        output_file = os.path.join(output_dir, f"{base_name}.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)
