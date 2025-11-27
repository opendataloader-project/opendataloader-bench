import opendataloader_pdf


def to_markdown(_, input_path, output_dir):
    opendataloader_pdf.convert(
        input_path=[input_path],
        output_dir=output_dir,
        format=["markdown"],
        quiet=True,
    )
