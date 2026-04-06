import os


def _patch_layout_from_file():
    """Monkey-patch unstructured_inference to avoid 'Operation on closed image' bug.

    The bug: ``DocumentLayout.from_file`` opens images with ``with Image.open(...)``
    but ``PageLayout.from_image`` sets ``page.image = None``, which releases the
    underlying file pointer. When the ``with`` block exits it tries to close an
    already-closed handle → ValueError.

    Fix: open without context manager; the image is freed inside from_image anyway.
    """
    from unstructured_inference.inference import layout as _layout
    from PIL import Image
    from typing import List, Optional, cast

    _orig_from_file = _layout.DocumentLayout.from_file.__func__

    @classmethod
    def _patched_from_file(cls, filename, fixed_layouts=None, pdf_image_dpi=200, password=None, **kwargs):
        import tempfile
        _layout.logger.info(f"Reading PDF for file: {filename} ...")
        with tempfile.TemporaryDirectory() as temp_dir:
            _image_paths = _layout.convert_pdf_to_image(
                filename=filename, dpi=pdf_image_dpi, output_folder=temp_dir,
                path_only=True, password=password,
            )
            image_paths = cast(List[str], _image_paths)
            number_of_pages = len(image_paths)
            pages = []
            if fixed_layouts is None:
                fixed_layouts = [None] * number_of_pages
            for i, (image_path, fixed_layout) in enumerate(zip(image_paths, fixed_layouts)):
                image = Image.open(image_path)
                page = _layout.PageLayout.from_image(
                    image, number=i + 1, document_filename=filename,
                    fixed_layout=fixed_layout, **kwargs,
                )
                pages.append(page)
            return cls.from_pages(pages)

    _layout.DocumentLayout.from_file = _patched_from_file


_patch_layout_from_file()

from unstructured.partition.pdf import partition_pdf


def to_markdown(doc_paths, input_path, output_dir):
    for doc_path in doc_paths:
        elements = partition_pdf(
            filename=str(doc_path),
            strategy="hi_res",
            languages=["kor", "eng"],
            infer_table_structure=True,
        )
        markdown_parts = []
        for element in elements:
            category = getattr(element, "category", None)
            text = str(element)
            if category == "Title":
                markdown_parts.append(f"# {text}")
            elif category == "Header":
                markdown_parts.append(f"## {text}")
            elif category == "Table":
                html = getattr(element.metadata, "text_as_html", None)
                if html:
                    markdown_parts.append(html)
                else:
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
