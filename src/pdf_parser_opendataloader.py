import opendataloader_pdf


def to_markdown(_, input_path, output_dir):
    opendataloader_pdf.convert(
        input_path=[input_path],
        output_dir=output_dir,
        format=["markdown"],
        table_method="cluster",
        image_output="off",
        quiet=True,
    )
