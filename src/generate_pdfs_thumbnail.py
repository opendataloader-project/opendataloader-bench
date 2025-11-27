import logging
from pathlib import Path
from pdf2image import convert_from_path


def export_first_page(pdf_path: Path, output_path: Path) -> None:
    """Render the first page of the PDF at a higher resolution and save as WebP."""
    try:
        images = convert_from_path(pdf_path, first_page=1, last_page=1)
        if images:
            images[0].save(output_path, "WEBP", lossless=True)
        else:
            logging.warning("No pages found in PDF: %s", pdf_path)

    except Exception as e:
        logging.error("Error processing %s: %s", pdf_path, e)
        raise


def run(project_root: Path | str) -> None:
    root_path = Path(project_root)
    pdf_dir = root_path / "pdfs"
    output_dir = root_path / "pdfs_thumbnail"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not pdf_dir.exists():
        raise FileNotFoundError(f"PDF directory not found: {pdf_dir}")

    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        logging.info("No PDF files found in %s", pdf_dir)
        return

    for pdf_file in pdf_files:
        output_file = output_dir / f"{pdf_file.stem}.webp"
        try:
            export_first_page(pdf_file, output_file)
            logging.info("Generated thumbnail for %s", pdf_file.name)
        except Exception as exc:  # noqa: BLE001
            logging.error("Failed to generate thumbnail for %s: %s", pdf_file.name, exc)


if __name__ == "__main__":
    # Get the absolute path to the project root
    project_root = Path(__file__).resolve().parent.parent

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    run(project_root)
