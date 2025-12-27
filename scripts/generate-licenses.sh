#!/bin/bash
# Generate third-party license files for Python dependencies

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Dataset section (manually maintained)
DATASETS_SECTION='## Datasets

| Name    | Source                                          | License |
|---------|-------------------------------------------------|---------|
| DP-Bench | https://huggingface.co/datasets/upstage/dp-bench | MIT     |

## Python Dependencies

'

echo "Generating THIRD_PARTY_NOTICES.md..."
echo -n "$DATASETS_SECTION" > THIRD_PARTY_NOTICES.md
uv run --with pip-licenses pip-licenses --format=markdown >> THIRD_PARTY_NOTICES.md

echo "Generating THIRD_PARTY_LICENSES.txt..."
uv run --with pip-licenses pip-licenses --format=plain-vertical --with-license-file --output-file=THIRD_PARTY_LICENSES.txt

echo "Done!"
ls -la THIRD_PARTY_*
