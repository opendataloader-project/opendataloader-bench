"""PDF parser using opendataloader-pdf.

Supports two modes:
- JAR mode: Set OPENDATALOADER_JAR env var to a local JAR path (for CI)
- Python mode: Uses installed opendataloader_pdf package (default)
"""

import os
import subprocess
import sys


def _run_jar(jar_path, input_path, output_dir):
    """Convert PDF using local JAR."""
    command = [
        "java", "-jar", jar_path,
        str(input_path),
        "--output-dir", str(output_dir),
        "--format", "markdown",
        "--table-method", "cluster",
        "--image-output", "off",
        "--quiet",
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error converting {input_path}:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)


def _run_python(input_path, output_dir):
    """Convert PDF using installed Python package."""
    import opendataloader_pdf

    opendataloader_pdf.convert(
        input_path=[input_path],
        output_dir=output_dir,
        format=["markdown"],
        table_method="cluster",
        image_output="off",
        quiet=True,
    )


def to_markdown(_, input_path, output_dir):
    jar_path = os.environ.get("OPENDATALOADER_JAR")
    if jar_path:
        _run_jar(jar_path, input_path, output_dir)
    else:
        _run_python(input_path, output_dir)
