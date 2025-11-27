#!/bin/bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd "${SCRIPT_DIR}/.." && pwd)
PYTHON_BIN=${PYTHON:-python}

ENGINES=(
    "docling"
    "markitdown"
    "opendataloader"
)

if [ "${#ENGINES[@]}" -eq 0 ]; then
  echo "No engines found to run powermetrics for." >&2
  exit 1
fi

cd "${PROJECT_ROOT}"

for ENGINE_NAME in "${ENGINES[@]}"; do
  echo "Collecting powermetrics for ${ENGINE_NAME}..."
  mkdir -p "prediction/${ENGINE_NAME}"

  sudo powermetrics --samplers cpu_power,gpu_power,ane_power -i 1000 > "prediction/${ENGINE_NAME}/powermetrics.txt" &
  PM_PID=$!

  set +e
  "${PYTHON_BIN}" src/pdf_parser.py --engine "${ENGINE_NAME}"
  PARSE_STATUS=$?
  set -e

  kill "${PM_PID}" 2>/dev/null || true
  wait "${PM_PID}" 2>/dev/null || true
  PM_PID=""

  if [ "${PARSE_STATUS}" -ne 0 ]; then
    echo "Parsing failed for ${ENGINE_NAME} (exit ${PARSE_STATUS})." >&2
    exit "${PARSE_STATUS}"
  fi
done

trap - EXIT
