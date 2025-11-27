import json
import os
from typing import Callable, Dict
from bs4 import BeautifulSoup


def _format_heading1(text: str) -> str:
    stripped = text.strip()
    return f"# {stripped}" if stripped else ""


def _format_list(text: str) -> str:
    stripped = text.strip()
    return f"- {stripped}" if stripped else ""


_CATEGORY_FORMATTERS: Dict[str, Callable[[str], str]] = {
    "heading1": _format_heading1,
    "list": _format_list,
}


def _format_content_by_category(category: str, text: str) -> str:
    formatter = _CATEGORY_FORMATTERS.get(category.lower())
    return formatter(text) if formatter else text


def extract_markdown_from_reference(json_path, output_dir):
    """
    Extracts content from a reference.json file and saves it to .md files.
    - For elements with category 'table', it uses the prettified html content wrapped in <table> tags.
    - For other elements, it prefers text content, adds a level-1 heading for 'Heading1',
      formats lists with leading hyphens, and leaves other categories as-is.

    Args:
        json_path (str): The path to the reference.json file.
        output_dir (str): The directory to save the output .md files.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for pdf_filename, content in data.items():
        all_content = []
        if "elements" in content:
            for element in content["elements"]:
                if "content" in element:
                    category = element.get("category", "").lower()
                    content_data = element["content"]
                    content_to_add = None

                    if category == "table":
                        html_content = content_data.get("html")
                        if html_content:
                            full_table_html = f"<table>{html_content}</table>"
                            soup = BeautifulSoup(full_table_html, "html.parser")
                            content_to_add = soup.prettify()
                    else:
                        text_content = content_data.get("text")
                        if text_content:
                            content_to_add = _format_content_by_category(
                                category, text_content
                            )

                    if content_to_add:
                        all_content.append(content_to_add)

        if all_content:
            output_filename = os.path.splitext(pdf_filename)[0] + ".md"
            output_path = os.path.join(output_dir, output_filename)

            with open(output_path, "w", encoding="utf-8") as md_file:
                md_file.write("\n\n".join(all_content))
            print(f"Successfully created {output_path}")


if __name__ == "__main__":
    # Get the absolute path to the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Construct the absolute paths for the input and output files
    json_file_path = os.path.join(project_root, "ground-truth", "reference.json")
    output_directory = os.path.join(project_root, "ground-truth", "markdown")

    extract_markdown_from_reference(json_file_path, output_directory)
