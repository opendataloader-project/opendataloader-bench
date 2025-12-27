#!/bin/bash
# Generate third-party license files for Python dependencies

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Generating THIRD_PARTY_NOTICES.md..."
uv run --with pip-licenses pip-licenses --format=markdown --output-file=THIRD_PARTY_NOTICES.md

echo "Generating THIRD_PARTY_LICENSES.txt..."
uv run --with pip-licenses pip-licenses --format=plain-vertical --with-license-file --output-file=THIRD_PARTY_LICENSES.txt

echo "Done!"
ls -la THIRD_PARTY_*
