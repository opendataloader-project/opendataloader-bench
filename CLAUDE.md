# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a benchmark suite for evaluating PDF-to-Markdown conversion engines. It measures reading order accuracy (NID), table fidelity (TEDS), heading hierarchy preservation (MHS), and extraction speed across 12 parsing engines.

## Commands

### Full Pipeline
```sh
uv run src/run.py                          # Quality benchmark (parse → evaluate → archive → chart)
uv run src/run.py --engine docling         # Single engine (skips if evaluation.json exists)
uv run src/run.py --engine docling --force # Force re-run
uv run src/run.py --mode speed             # Speed benchmark only
uv run src/run.py --mode all               # Both quality and speed
```

### CI Mode (used by opendataloader-pdf CI)
```sh
OPENDATALOADER_JAR=/path/to/jar uv run src/run.py --engine opendataloader --check-regression
```

### Individual Stages
```sh
uv run src/pdf_parser.py             # Convert PDFs to Markdown (all engines)
uv run src/evaluator.py              # Evaluate predictions against ground truth
uv run src/generate_benchmark_chart.py  # Generate comparison charts (no engine deps needed)
uv run src/generate_history.py       # Archive evaluation results
```

### Tests
```sh
uv run pytest                        # Run all tests
uv run pytest tests/test_evaluator_table.py  # Single test file
```

## Architecture

### Dependency Strategy
Engine libraries are **optional dependencies** to avoid conflicts. Base deps (apted, matplotlib, rapidfuzz, etc.) are always installed for evaluation/charting. Each engine is a separate optional group:
```sh
uv sync --extra opendataloader   # Install one engine
uv sync --extra all-safe         # All permissive-license engines
```
Chart generation works with base deps only (reads evaluation.json files).

### Engine Registry (engine_registry.py)
Uses **lazy imports** via `get_engine_handler()`. Engines not installed are gracefully skipped. `ENGINE_DISPATCH` is a `_LazyDispatch` dict for backward compatibility.

### Adding a New Engine
1. Create `src/pdf_parser_<name>.py` with `to_markdown(document_paths, input_path, output_dir)` function
2. Add to `ENGINES` and `_ENGINE_MODULES` dicts in `engine_registry.py`
3. Add optional dependency group in `pyproject.toml`
4. For speed benchmark: add parser class in `src/speed_benchmark/parsers/<name>.py`

### Pipeline Flow
1. **pdf_parser.py** → dispatches to engine-specific handlers via lazy import
2. **evaluator.py** → runs NID/TEDS/MHS evaluators, produces `evaluation.json`
3. **generate_benchmark_chart.py** → horizontal bar charts from evaluation.json (filtered by ENGINES registry)
4. **run.py** → orchestrates quality/speed/all modes with skip logic

### Speed Benchmark (src/speed_benchmark/)
Migrated from odl-speed-benchmark. Measures latency and peak memory using tracemalloc.
- `runner.py` — core measurement loop with warmup
- `report.py` — chart generation + JSON output
- `parsers/` — lazy-loaded parser registry

### License Tiers
- **Safe** (direct import): opendataloader, docling, markitdown, unstructured, edgeparse, pypdf, liteparse
- **AGPL/GPL** (subprocess only): MinerU, PyMuPDF, marker
- **Proprietary** (CLI only, not in deps): nutrient/PSPDFKit

### Directory Structure
- `pdfs/` — Input PDF corpus (200 documents)
- `ground-truth/markdown/` — Reference Markdown files
- `prediction/<engine>/markdown/` — Engine outputs
- `prediction/<engine>/evaluation.json` — Evaluation results
- `history/<yymmdd>/` — Archived evaluation snapshots
- `charts/` — Generated benchmark visualizations
- `src/speed_benchmark/` — Speed benchmark module
- `speed_benchmark_data/` — PDF corpus for speed tests
- `speed_results/` — Speed benchmark JSON results
