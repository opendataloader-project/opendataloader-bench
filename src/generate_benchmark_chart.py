"""Generate benchmark bar charts from evaluation.json files."""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


DEFAULT_PREDICTION_ROOT = Path("prediction")
DEFAULT_OUTPUT_PATH = Path("charts/benchmark.png")
MIN_BAR_HEIGHT = 0.01

# Colors for accuracy charts
WINNER_COLOR = "#4C78A8"      # blue for 1st place
OTHER_COLOR = "#94A3B8"       # medium slate for others
# Colors for time chart
TIME_WINNER_COLOR = "#F28E2C" # orange for 1st place
TIME_OTHER_COLOR = "#FDBA74"  # medium orange for others


@dataclass
class EngineMetrics:
    """Container for aggregated scores per engine/version combination."""

    label: str
    overall: Optional[float]
    nid: Optional[float]
    nid_s: Optional[float]
    teds: Optional[float]
    teds_s: Optional[float]
    mhs: Optional[float]
    mhs_s: Optional[float]
    elapsed_per_page: Optional[float]


def _load_evaluation_metrics(prediction_root: Path) -> List[EngineMetrics]:
    """Load aggregated metrics from every engine/version evaluation file."""

    engines: List[EngineMetrics] = []
    for engine_dir in sorted(prediction_root.iterdir()):
        if not engine_dir.is_dir():
            continue
        evaluation_path = engine_dir / "evaluation.json"
        if not evaluation_path.is_file():
            logging.debug("Skipping %s (missing evaluation.json)", engine_dir)
            continue

        try:
            with evaluation_path.open(encoding="utf-8") as f:
                payload: Dict[str, Dict[str, Dict[str, float]]] = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logging.warning("Failed to read %s: %s", evaluation_path, exc)
            continue

        scores = payload.get("metrics", {}).get("score", {})
        summary = payload.get("summary", {})
        engine_name = summary.get("engine_name", "unknown")
        elapsed_per_page = summary.get("elapsed_per_doc")
        engines.append(
            EngineMetrics(
                label=engine_name,
                overall=_as_float(scores.get("overall_mean")),
                nid=_as_float(scores.get("nid_mean")),
                nid_s=_as_float(scores.get("nid_s_mean")),
                teds=_as_float(scores.get("teds_mean")),
                teds_s=_as_float(scores.get("teds_s_mean")),
                mhs=_as_float(scores.get("mhs_mean")),
                mhs_s=_as_float(scores.get("mhs_s_mean")),
                elapsed_per_page=_as_float(elapsed_per_page),
            )
        )

    return engines


def _as_float(value: object) -> Optional[float]:
    """Convert JSON value to float when possible."""

    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _add_value_labels(ax, bars, values: Sequence[Optional[float]]) -> None:
    """Annotate bar tops with numeric values."""

    for bar, value in zip(bars, values):
        if value is None:
            continue
        height = bar.get_height()
        ax.annotate(
            f"{value:.2f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=11,
        )


def _ensure_min_bar_height(bars, values: Sequence[Optional[float]]) -> None:
    """Ensure visible bars even when the underlying value is zero."""

    for bar, value in zip(bars, values):
        if value is None:
            continue
        if bar.get_height() <= 0:
            bar.set_height(MIN_BAR_HEIGHT)


def _plot_single_metric(
    ax,
    engines: List[EngineMetrics],
    values: List[Optional[float]],
    title: str,
) -> None:
    """Plot a single bar chart for one metric."""

    sortable = list(zip(engines, values))
    sortable.sort(key=lambda item: (item[1] is None, -(item[1] or 0.0)))
    sorted_engines = [engine for engine, _ in sortable]
    sorted_values = [value for _, value in sortable]

    labels = [engine.label for engine in sorted_engines]
    index = range(len(labels))
    clean_values = [value or 0.0 for value in sorted_values]
    colors = [WINNER_COLOR if i == 0 else OTHER_COLOR for i in range(len(labels))]
    bars = ax.bar(labels, clean_values, color=colors)
    _ensure_min_bar_height(bars, sorted_values)
    _add_value_labels(ax, bars, sorted_values)
    ax.set_ylim(0, 1)
    ax.set_title(title, fontsize=14)
    ax.set_xticks(list(index))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=12)
    ax.set_ylabel("Score", fontsize=12)


def _plot_grouped_metric(
    ax,
    engines: List[EngineMetrics],
    primary: List[Optional[float]],
    secondary: List[Optional[float]],
    title: str,
    primary_label: str,
    secondary_label: str,
) -> None:
    """Plot grouped bars for a pair of related metrics (e.g. TEDS/TEDS-S)."""

    combined = list(zip(engines, primary, secondary))
    combined.sort(key=lambda item: (item[1] is None, -(item[1] or 0.0)))
    sorted_engines = [engine for engine, _, _ in combined]
    sorted_primary = [value for _, value, _ in combined]
    sorted_secondary = [value for _, _, value in combined]

    labels = [engine.label for engine in sorted_engines]
    index = range(len(labels))
    width = 0.35

    primary_values = [value or 0.0 for value in sorted_primary]
    secondary_values = [value or 0.0 for value in sorted_secondary]

    bars1 = ax.bar(
        [i - width / 2 for i in index],
        primary_values,
        width,
        label=primary_label,
        color="#59A14F",
    )
    bars2 = ax.bar(
        [i + width / 2 for i in index],
        secondary_values,
        width,
        label=secondary_label,
        color="#E15759",
    )

    _ensure_min_bar_height(bars1, sorted_primary)
    _ensure_min_bar_height(bars2, sorted_secondary)

    _add_value_labels(ax, bars1, sorted_primary)
    _add_value_labels(ax, bars2, sorted_secondary)

    ax.set_ylim(0, 1)
    ax.set_title(title, fontsize=14)
    ax.set_ylabel("Score", fontsize=12)
    ax.set_xticks(list(index))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=12)
    ax.legend(fontsize=11)


def _plot_time_metric(
    ax,
    engines: List[EngineMetrics],
    values: List[Optional[float]],
) -> None:
    """Plot extraction time per page."""

    sortable = list(zip(engines, values))
    sortable.sort(
        key=lambda item: (
            item[1] is None,
            item[1] if item[1] is not None else float("inf"),
        )
    )
    sorted_engines = [engine for engine, _ in sortable]
    sorted_values = [value for _, value in sortable]

    labels = [engine.label for engine in sorted_engines]
    index = range(len(labels))
    clean_values = [value or 0.0 for value in sorted_values]
    colors = [TIME_WINNER_COLOR if i == 0 else TIME_OTHER_COLOR for i in range(len(labels))]
    bars = ax.bar(labels, clean_values, color=colors)
    _ensure_min_bar_height(bars, sorted_values)
    _add_value_labels(ax, bars, sorted_values)
    ax.set_title("Extraction Time Per Page (s)", fontsize=14)
    ax.set_ylabel("Seconds", fontsize=12)
    ax.set_xticks(list(index))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=12)


def _save_individual_chart(
    plotter: Callable[..., None],
    plot_args: Sequence[object],
    output_path: Path,
) -> None:
    """Render and persist a single chart using an existing plotting helper."""

    fig, ax = plt.subplots(figsize=(6, 4))
    plotter(ax, *plot_args)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    logging.info("Saved individual chart to %s", output_path)


def generate_charts(prediction_root: Path, output_path: Path) -> Path:
    """Create the benchmark chart and save it to disk."""

    engines = _load_evaluation_metrics(prediction_root)
    if not engines:
        raise FileNotFoundError(
            f"No evaluation.json files found under {prediction_root.resolve()}"
        )

    engines.sort(
        key=lambda metric: metric.overall if metric.overall is not None else -1.0,
        reverse=True,
    )

    plt.style.use("ggplot")
    fig, axes = plt.subplots(3, 2, figsize=(12, 10), constrained_layout=True)

    overall_values = [engine.overall for engine in engines]
    nid_values = [engine.nid for engine in engines]
    teds_values = [engine.teds for engine in engines]
    mhs_values = [engine.mhs for engine in engines]
    elapsed_values = [engine.elapsed_per_page for engine in engines]

    _plot_single_metric(
        axes[0, 0],
        engines,
        overall_values,
        "Extraction Accuracy",
    )

    _plot_time_metric(
        axes[0, 1],
        engines,
        elapsed_values,
    )

    _plot_single_metric(
        axes[1, 0],
        engines,
        nid_values,
        "Reading Order (NID)",
    )

    _plot_single_metric(
        axes[1, 1],
        engines,
        teds_values,
        "Table Structure (TEDS)",
    )

    _plot_single_metric(
        axes[2, 0],
        engines,
        mhs_values,
        "Heading Level (MHS)",
    )

    axes[2, 1].axis("off")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.suptitle("PDF-to-Markdown Benchmark", fontsize=18)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)

    logging.info("Saved benchmark chart to %s", output_path)

    suffix = "".join(output_path.suffixes) or ".png"
    stem = output_path.stem
    chart_specs: List[Tuple[str, Callable[..., None], Tuple[object, ...]]] = [
        (
            "overall",
            _plot_single_metric,
            (engines, overall_values, "Extraction Accuracy"),
        ),
        (
            "reading-order",
            _plot_single_metric,
            (engines, nid_values, "Reading Order (NID)"),
        ),
        (
            "table-structure",
            _plot_single_metric,
            (engines, teds_values, "Table Structure (TEDS)"),
        ),
        (
            "heading-level",
            _plot_single_metric,
            (engines, mhs_values, "Heading Level (MHS)"),
        ),
        (
            "extraction-time",
            _plot_time_metric,
            (engines, elapsed_values),
        ),
    ]

    for suffix_name, plotter, plot_args in chart_specs:
        individual_path = output_path.parent / f"{stem}_{suffix_name}{suffix}"
        _save_individual_chart(plotter, plot_args, individual_path)

    return output_path


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate bar charts from evaluation.json files"
    )
    parser.add_argument(
        "--prediction-root",
        type=Path,
        default=DEFAULT_PREDICTION_ROOT,
        help="Directory containing engine prediction outputs",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Destination file for the generated chart image",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging verbosity (e.g. INFO, DEBUG)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = _parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    output = generate_charts(args.prediction_root, args.output)
    print(output)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
