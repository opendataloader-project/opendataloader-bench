"""PDF parser using opendataloader-pdf with hybrid mode (hancom backend).

Requirements:
- Hancom API access
- OPENDATALOADER_JAR env var set to the CLI JAR path

Environment Variables:
    OPENDATALOADER_JAR: Path to opendataloader-pdf CLI JAR (required)
    HANCOM_URL: Override URL for the Hancom API
    HYBRID_TIMEOUT: Request timeout in milliseconds (default: 600000)
"""

import os
import subprocess
import sys


DEFAULT_URL = "https://dataloader.cloud.hancom.com/studio-lite/api"


def to_markdown(_, input_path, output_dir):
    """Convert PDF to Markdown using hybrid mode with hancom backend."""
    jar_path = os.environ.get("OPENDATALOADER_JAR")
    if not jar_path:
        raise EnvironmentError(
            "OPENDATALOADER_JAR env var not set. Set it to the CLI JAR path."
        )

    backend_url = os.environ.get("HANCOM_URL", DEFAULT_URL)
    timeout_ms = os.environ.get("HYBRID_TIMEOUT", "600000")

    command = [
        "java", "-jar", jar_path,
        str(input_path),
        "--output-dir", str(output_dir),
        "--format", "markdown",
        "--image-output", "off",
        "--quiet",
        "--hybrid", "hancom",
        "--hybrid-url", backend_url,
        "--hybrid-timeout", timeout_ms,
        "--hybrid-fallback",
        "--hybrid-mode", "full",
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error converting {input_path} (hancom hybrid mode):", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
