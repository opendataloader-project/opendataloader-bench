import atexit
import logging
import subprocess
import sys
import time
import urllib.request
import urllib.error

import opendataloader_pdf

HYBRID_URL = "http://localhost:5002"
HEALTH_ENDPOINT = f"{HYBRID_URL}/health"
STARTUP_TIMEOUT = 120

logger = logging.getLogger(__name__)

_server_process = None


def _is_server_running():
    """Check if the hybrid backend is reachable via the health endpoint."""
    try:
        req = urllib.request.Request(HEALTH_ENDPOINT, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError):
        return False


def _stop_server():
    """Terminate the server process if we started it."""
    global _server_process
    if _server_process and _server_process.poll() is None:
        logger.info("Stopping hybrid backend server (pid=%d)", _server_process.pid)
        _server_process.terminate()
        try:
            _server_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _server_process.kill()
        _server_process = None


def _ensure_server():
    """Start the hybrid backend if it is not already running."""
    global _server_process

    if _is_server_running():
        logger.info("Hybrid backend already running at %s", HYBRID_URL)
        return

    logger.info("Hybrid backend not running — starting opendataloader-pdf-hybrid ...")
    _server_process = subprocess.Popen(
        [sys.executable, "-m", "opendataloader_pdf.hybrid_server"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    atexit.register(_stop_server)

    deadline = time.monotonic() + STARTUP_TIMEOUT
    while time.monotonic() < deadline:
        if _server_process.poll() is not None:
            stderr = _server_process.stderr.read().decode(errors="replace")
            raise RuntimeError(
                f"Hybrid backend exited unexpectedly (rc={_server_process.returncode}):\n{stderr}"
            )
        if _is_server_running():
            logger.info("Hybrid backend is ready at %s", HYBRID_URL)
            return
        time.sleep(2)

    _stop_server()
    raise TimeoutError(
        f"Hybrid backend did not become ready within {STARTUP_TIMEOUT}s"
    )


def to_markdown(_, input_path, output_dir):
    _ensure_server()
    opendataloader_pdf.convert(
        input_path=[input_path],
        output_dir=output_dir,
        format=["markdown"],
        hybrid="docling-fast",
        image_output="off",
        quiet=True,
    )
