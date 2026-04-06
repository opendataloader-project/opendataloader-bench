"""One-shot runner that executes the full benchmark pipeline."""

from __future__ import annotations

import argparse
import json
import logging
import os
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


def check_regression(eval_data: dict, thresholds_path: Path) -> bool:
    """Check if evaluation results meet threshold requirements.

    Returns:
        True if all thresholds are met, False otherwise
    """
    if not thresholds_path.exists():
        logging.warning("Thresholds file not found: %s", thresholds_path)
        return True

    with thresholds_path.open(encoding="utf-8") as f:
        thresholds = json.load(f)

    scores = eval_data.get("metrics", {}).get("score", {})
    table_detection = eval_data.get("table_detection", {})
    speed = eval_data.get("speed", {})
    tol = thresholds.get("regression_tolerance", 0)

    failures = []

    nid = scores.get("nid_mean")
    nid_thresh = thresholds.get("nid")
    if nid is not None and nid_thresh is not None and nid < nid_thresh - tol:
        failures.append(f"NID {nid:.4f} < {nid_thresh} - {tol}")

    teds = scores.get("teds_mean")
    teds_thresh = thresholds.get("teds")
    if teds is not None and teds_thresh is not None and teds < teds_thresh - tol:
        failures.append(f"TEDS {teds:.4f} < {teds_thresh} - {tol}")

    mhs = scores.get("mhs_mean")
    mhs_thresh = thresholds.get("mhs")
    if mhs is not None and mhs_thresh is not None and mhs < mhs_thresh - tol:
        failures.append(f"MHS {mhs:.4f} < {mhs_thresh} - {tol}")

    td_f1 = table_detection.get("f1")
    td_f1_thresh = thresholds.get("table_detection_f1")
    if td_f1 is not None and td_f1_thresh is not None and td_f1 < td_f1_thresh - tol:
        failures.append(f"Table Detection F1 {td_f1:.4f} < {td_f1_thresh} - {tol}")

    elapsed_per_doc = speed.get("elapsed_per_doc")
    elapsed_thresh = thresholds.get("elapsed_per_doc")
    if elapsed_per_doc is not None and elapsed_thresh is not None and elapsed_per_doc > elapsed_thresh:
        failures.append(f"Speed {elapsed_per_doc:.2f}s/doc > {elapsed_thresh}s/doc")

    triage = eval_data.get("triage", {})
    if triage:
        triage_recall = triage.get("recall")
        triage_recall_thresh = thresholds.get("triage_recall")
        if triage_recall is not None and triage_recall_thresh is not None and triage_recall < triage_recall_thresh - tol:
            failures.append(f"Triage Recall {triage_recall:.4f} < {triage_recall_thresh} - {tol}")

        triage_fn = triage.get("fn_count")
        triage_fn_max = thresholds.get("triage_fn_max")
        if triage_fn is not None and triage_fn_max is not None and triage_fn > triage_fn_max:
            failures.append(f"Triage FN {triage_fn} > {triage_fn_max}")

    if failures:
        logging.error("Regression detected:")
        for failure in failures:
            logging.error("  - %s", failure)
        return False

    logging.info("All thresholds met.")
    return True


def print_summary(eval_data: dict) -> None:
    """Print a summary of evaluation results."""
    scores = eval_data.get("metrics", {}).get("score", {})
    table_detection = eval_data.get("table_detection", {})
    speed = eval_data.get("speed", {})
    triage = eval_data.get("triage", {})

    print("\n" + "=" * 50)
    print("BENCHMARK RESULTS")
    print("=" * 50)

    nid = scores.get("nid_mean")
    teds = scores.get("teds_mean")
    mhs = scores.get("mhs_mean")
    td_f1 = table_detection.get("f1")
    td_precision = table_detection.get("precision")
    td_recall = table_detection.get("recall")
    elapsed_per_doc = speed.get("elapsed_per_doc")
    total_elapsed = speed.get("total_elapsed")
    document_count = speed.get("document_count")

    print(f"NID  (Reading Order):     {nid:.4f}" if nid else "NID:  N/A")
    print(f"TEDS (Table Structure):   {teds:.4f}" if teds else "TEDS: N/A")
    print(f"MHS  (Heading Structure): {mhs:.4f}" if mhs else "MHS:  N/A")
    print()
    print("Table Detection:")
    td_accuracy = table_detection.get("accuracy")
    print(f"  Precision: {td_precision:.4f}" if td_precision else "  Precision: N/A")
    print(f"  Recall:    {td_recall:.4f}" if td_recall else "  Recall: N/A")
    print(f"  F1:        {td_f1:.4f}" if td_f1 else "  F1: N/A")
    print(f"  Accuracy:  {td_accuracy:.4f}" if td_accuracy else "  Accuracy: N/A")
    print()
    print("Speed:")
    print(f"  Per Document: {elapsed_per_doc:.2f}s" if elapsed_per_doc else "  Per Document: N/A")
    print(f"  Total:        {total_elapsed:.1f}s ({document_count} docs)" if total_elapsed else "  Total: N/A")

    if triage:
        print()
        print("Triage (Hybrid Mode):")
        tr_recall = triage.get("recall")
        tr_precision = triage.get("precision")
        tr_f1 = triage.get("f1")
        print(f"  Recall:    {tr_recall:.4f}" if tr_recall is not None else "  Recall: N/A")
        print(f"  Precision: {tr_precision:.4f}" if tr_precision is not None else "  Precision: N/A")
        print(f"  F1:        {tr_f1:.4f}" if tr_f1 is not None else "  F1: N/A")

    print("=" * 50 + "\n")


def _should_skip_engine(engine_name: str, prediction_root: Path, force: bool) -> bool:
    """Return True if the engine already has evaluation data and --force is not set."""
    if force:
        return False
    eval_path = prediction_root / engine_name / "evaluation.json"
    if eval_path.is_file():
        logging.info("Skipping %s (evaluation.json exists, use --force to rerun)", engine_name)
        return True
    return False



def run_pipeline(args: argparse.Namespace) -> Optional[dict]:
    """Execute parsing, evaluation, history archival, and chart generation."""

    project_root = Path(__file__).parent.parent.resolve()
    input_dir = _resolve_path(args.input_dir, project_root)
    ground_truth_dir = _resolve_path(args.ground_truth_dir, project_root)
    prediction_root = _resolve_path(args.prediction_root, project_root)

    # Set JAR path env var if provided
    if hasattr(args, "jar_path") and args.jar_path:
        os.environ["OPENDATALOADER_JAR"] = str(Path(args.jar_path).resolve())

    engines = _select_engine(args.engine)
    if not engines:
        raise ValueError("No engines selected for processing.")

    force = getattr(args, "force", False)

    logging.info("Starting PDF parsing for engines: %s", ", ".join(engines))
    for engine_name in engines:
        if _should_skip_engine(engine_name, prediction_root, force):
            continue
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

    # Load evaluation results for additional metrics
    eval_path = evaluation_paths[0]
    with eval_path.open(encoding="utf-8") as f:
        eval_data = json.load(f)

    # Table detection evaluation
    reference_path = ground_truth_dir / "reference.json"
    if reference_path.exists():
        from evaluator_table_detection import evaluate_table_detection_batch

        engine_name = eval_path.parent.name
        prediction_markdown_dir = prediction_root / engine_name / "markdown"
        table_detection_metrics = evaluate_table_detection_batch(
            reference_path, prediction_markdown_dir
        )
        eval_data["table_detection"] = table_detection_metrics.to_dict()
        logging.info("Table detection: F1=%.4f", table_detection_metrics.f1 or 0)

    # Speed metrics from summary.json
    engine_name = eval_path.parent.name
    summary_path = prediction_root / engine_name / "summary.json"
    if summary_path.exists():
        with summary_path.open(encoding="utf-8") as f:
            summary_data = json.load(f)
        eval_data["speed"] = {
            "total_elapsed": summary_data.get("total_elapsed"),
            "elapsed_per_doc": summary_data.get("elapsed_per_doc"),
            "document_count": summary_data.get("document_count"),
            "processor": summary_data.get("processor"),
        }

    # Triage evaluation (for hybrid engines)
    if reference_path.exists():
        from evaluator_triage import evaluate_triage_batch

        prediction_engine_dir = prediction_root / engine_name
        triage_metrics = evaluate_triage_batch(reference_path, prediction_engine_dir)
        if triage_metrics.total_pages_evaluated > 0:
            eval_data["triage"] = triage_metrics.to_dict()
            logging.info("Triage: recall=%.4f, fn=%d",
                         triage_metrics.recall or 0, triage_metrics.fn_count)

    # Save updated evaluation
    with eval_path.open("w", encoding="utf-8") as f:
        json.dump(eval_data, f, indent=2, ensure_ascii=False)

    # Skip history/chart in CI mode
    if args.check_regression:
        return eval_data

    # History archival
    history_root = _resolve_path(args.history_root, project_root)
    chart_output = _resolve_path(args.chart_output, project_root)

    date_folder = _resolve_history_date(args.history_date)
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
        logging.info("[%s] Archived evaluation to %s", engine_name, archived)

    logging.info("Generating benchmark charts...")
    chart_path = generate_charts(prediction_root, chart_output)
    logging.info("Benchmark chart written to %s", chart_path)

    return eval_data


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
    parser.add_argument(
        "--check-regression",
        action="store_true",
        help="Check results against thresholds and exit with error if failed. Skips history/chart generation.",
    )
    parser.add_argument(
        "--thresholds",
        default="thresholds.json",
        help="Path to thresholds JSON file (default: thresholds.json in project root).",
    )
    parser.add_argument(
        "--jar-path",
        default=None,
        help="Path to opendataloader-pdf CLI JAR for JAR-based execution (sets OPENDATALOADER_JAR).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-run even if evaluation.json already exists for the engine.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = _parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    try:
        eval_data = run_pipeline(args)

        if eval_data:
            print_summary(eval_data)

        if args.check_regression and eval_data:
            project_root = Path(__file__).parent.parent.resolve()
            thresholds_path = _resolve_path(args.thresholds, project_root)
            if not check_regression(eval_data, thresholds_path):
                raise SystemExit(1)

    except Exception as exc:  # pragma: no cover - CLI entry point
        logging.error("Pipeline failed: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
