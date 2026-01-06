# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a benchmark suite for evaluating PDF-to-Markdown conversion engines. It measures reading order accuracy, table fidelity, and heading hierarchy preservation across multiple parsing engines (opendataloader, docling, markitdown).

## Commands

### Full Pipeline
```sh
uv run src/run.py                    # Run complete benchmark: parse → evaluate → archive → chart
uv run src/run.py --engine docling   # Run for single engine
```

### Individual Stages
```sh
uv run src/pdf_parser.py             # Convert PDFs to Markdown (all engines)
uv run src/evaluator.py              # Evaluate predictions against ground truth
uv run src/generate_benchmark_chart.py  # Generate comparison charts
uv run src/generate_history.py       # Archive evaluation results
```

### Targeting Specific Documents
```sh
uv run src/pdf_parser.py --engine opendataloader --doc-id 01030000000001
uv run src/evaluator.py --engine opendataloader --doc-id 01030000000001
```

### Tests
```sh
uv run pytest                        # Run all tests
uv run pytest tests/test_evaluator_table.py  # Single test file
```

## Architecture

### Pipeline Flow
1. **pdf_parser.py** - Orchestrates PDF→Markdown conversion, dispatches to engine-specific handlers
2. **engine_registry.py** - Central registry mapping engine names to versions and handler functions
3. **evaluator.py** - Runs all metric evaluators and produces `evaluation.json` per engine

### Engine Handlers
Located in `src/pdf_parser_*.py`. Each implements a `to_markdown(document_paths, input_path, output_dir)` function. To add a new engine:
1. Create `src/pdf_parser_<name>.py` with `to_markdown()` function
2. Register in `engine_registry.py` (ENGINES dict + ENGINE_DISPATCH dict)

### Evaluation Metrics
Each evaluator returns `(score, structure_only_score)` tuples:
- **evaluator_reading_order.py** - NID/NID-S using normalized Indel distance (rapidfuzz)
- **evaluator_table.py** - TEDS/TEDS-S using tree edit distance (APTED algorithm)
- **evaluator_heading_level.py** - MHS/MHS-S comparing heading structure trees

### Shared Utility
**converter_markdown_table.py** - Converts Markdown tables to HTML for consistent evaluation across all metrics.

### Directory Structure
- `pdfs/` - Input PDF corpus (200 documents)
- `ground-truth/markdown/` - Reference Markdown files
- `prediction/<engine>/markdown/` - Engine outputs
- `prediction/<engine>/evaluation.json` - Evaluation results
- `history/<yymmdd>/` - Archived evaluation snapshots
- `charts/` - Generated benchmark visualizations
