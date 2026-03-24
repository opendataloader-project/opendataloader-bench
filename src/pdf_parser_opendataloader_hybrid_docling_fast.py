"""PDF parser using opendataloader-pdf with hybrid mode (docling-fast backend).

Requirements:
- docling-fast server running: pip install opendataloader-pdf[hybrid] && opendataloader-pdf-hybrid
- OPENDATALOADER_JAR env var set to the CLI JAR path

Usage:
    opendataloader-pdf-hybrid &
    OPENDATALOADER_JAR=/path/to/jar uv run python src/run.py --engine opendataloader-hybrid-docling-fast
"""

import os
import subprocess
import sys


DEFAULT_URL = "http://localhost:5002"


def to_markdown(_, input_path, output_dir):
    """Convert PDF to Markdown using hybrid mode with docling-fast backend.

    Environment Variables:
        OPENDATALOADER_JAR: Path to opendataloader-pdf CLI JAR (required)
        DOCLING_URL: Override URL for the backend server. Default: http://localhost:5002
        HYBRID_TIMEOUT: Request timeout in milliseconds. Default: 600000
    """
    jar_path = os.environ.get("OPENDATALOADER_JAR")
    if not jar_path:
        raise EnvironmentError(
            "OPENDATALOADER_JAR env var not set. Set it to the CLI JAR path."
        )

    backend_url = os.environ.get("DOCLING_URL", DEFAULT_URL)
    timeout_ms = os.environ.get("HYBRID_TIMEOUT", "600000")

    command = [
        "java", "-jar", jar_path,
        str(input_path),
        "--output-dir", str(output_dir),
        "--format", "markdown",
        "--image-output", "off",
        "--quiet",
        "--hybrid", "docling-fast",
        "--hybrid-url", backend_url,
        "--hybrid-timeout", timeout_ms,
        "--hybrid-fallback",
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error converting {input_path} (hybrid mode):", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
