"""One-shot runner that executes the full PDF-to-Markdown benchmark pipeline."""

from __future__ import annotations

import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence

from evaluator import (
    DEFAULT_GT_DIR,
    DEFAULT_OUTPUT_FILENAME,
    DEFAULT_PREDICTION_ROOT,
    run as evaluate_run,
)
from engine_registry import ENGINES
from generate_benchmark_chart import DEFAULT_OUTPUT_PATH, generate_charts
from generate_history import YYMMDD_PATTERN, archive_evaluation
from pdf_parser import DEFAULT_INPUT_DIR, process_markdown


def _resolve_path(value: str, project_root: Path) -> Path:
    """Return ``value`` as an absolute Path anchored at the repository root."""

    path = Path(value)
    return path if path.is_absolute() else project_root / path


def _select_engine(requested: Optional[str]) -> List[str]:
    """Determine which engine(s) to run; only zero or one selection is allowed."""

    available = list(ENGINES.keys())
    if not requested:
        return available
    if requested not in ENGINES:
        raise ValueError(
            f"Unknown engine '{requested}'. Available engines: {', '.join(available)}"
        )
    return [requested]


def _resolve_history_date(date_arg: Optional[str]) -> str:
    if date_arg is None:
        return datetime.now().strftime("%y%m%d")
    if not YYMMDD_PATTERN.match(date_arg):
        raise ValueError("history-date must be 6 digits in yymmdd format (yymmdd)")
    return date_arg


def run_pipeline(args: argparse.Namespace) -> None:
    """Execute parsing, evaluation, history archival, and chart generation."""

    project_root = Path(__file__).parent.parent.resolve()
    input_dir = _resolve_path(args.input_dir, project_root)
    ground_truth_dir = _resolve_path(args.ground_truth_dir, project_root)
    prediction_root = _resolve_path(args.prediction_root, project_root)
    history_root = _resolve_path(args.history_root, project_root)
    chart_output = _resolve_path(args.chart_output, project_root)

    engines = _select_engine(args.engine)
    if not engines:
        raise ValueError("No engines selected for processing.")

    logging.info("Starting PDF parsing for engines: %s", ", ".join(engines))
    for engine_name in engines:
        logging.info("Processing PDFs with %s", engine_name)
        process_markdown(engine_name, str(input_dir), doc_id=args.doc_id)

    logging.info("Running evaluator...")
    evaluation_paths: List[Path] = []
    for engine_name in engines:
        generated = evaluate_run(
            str(ground_truth_dir),
            str(prediction_root),
            args.evaluation_filename,
            target_engine=engine_name,
            target_doc_id=args.doc_id,
        )
        evaluation_paths.extend(generated)

    if not evaluation_paths:
        raise RuntimeError("Evaluation stage did not produce any reports.")

    date_folder = _resolve_history_date(args.history_date)
    archived_paths: List[Path] = []
    logging.info("Archiving evaluation results under history/%s", date_folder)
    for evaluation_path in evaluation_paths:
        engine_name = evaluation_path.parent.name
        archived = archive_evaluation(
            engine=engine_name,
            prediction_root=prediction_root,
            history_root=history_root,
            date_folder=date_folder,
            overwrite=args.history_overwrite,
        )
        archived_paths.append(archived)
        logging.info("[%s] Archived evaluation to %s", engine_name, archived)

    logging.info("Generating benchmark charts...")
    chart_path = generate_charts(prediction_root, chart_output)
    logging.info("Benchmark chart written to %s", chart_path)


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run PDF parsing, evaluation, history archival, and benchmark chart generation in one step."
        )
    )
    parser.add_argument(
        "--input-dir",
        default=DEFAULT_INPUT_DIR,
        help="Directory containing PDFs to parse (defaults to ./pdfs).",
    )
    parser.add_argument(
        "--engine",
        default=None,
        help="Engine name to process. If omitted, every available engine is processed.",
    )
    parser.add_argument(
        "--doc-id",
        default=None,
        help="Restrict parsing/evaluation to a single document identifier.",
    )
    parser.add_argument(
        "--ground-truth-dir",
        default=DEFAULT_GT_DIR,
        help="Directory that stores ground-truth markdown files.",
    )
    parser.add_argument(
        "--prediction-root",
        default=DEFAULT_PREDICTION_ROOT,
        help="Root directory containing prediction outputs (defaults to ./prediction).",
    )
    parser.add_argument(
        "--evaluation-filename",
        default=DEFAULT_OUTPUT_FILENAME,
        help="Filename for generated evaluation payloads (default: evaluation.json).",
    )
    parser.add_argument(
        "--history-root",
        default="history",
        help="History archive root (defaults to ./history).",
    )
    parser.add_argument(
        "--history-date",
        default=None,
        help="History folder (yymmdd). Defaults to today's date if omitted.",
    )
    parser.add_argument(
        "--history-overwrite",
        dest="history_overwrite",
        action="store_true",
        default=True,
        help="Overwrite existing history files (default behavior).",
    )
    parser.add_argument(
        "--history-no-overwrite",
        dest="history_overwrite",
        action="store_false",
        help="Abort if the history target already contains evaluation.json.",
    )
    parser.add_argument(
        "--chart-output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Destination path for the combined benchmark chart image.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging verbosity (e.g. INFO, DEBUG).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = _parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    try:
        run_pipeline(args)
    except Exception as exc:  # pragma: no cover - CLI entry point
        logging.error("Pipeline failed: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
