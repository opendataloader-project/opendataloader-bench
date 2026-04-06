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
MIN_BAR_WIDTH = 0.01

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
    """Load aggregated metrics from every registered engine's evaluation file."""

    from engine_registry import ALL_CHART_ENGINES

    engines: List[EngineMetrics] = []
    for engine_dir in sorted(prediction_root.iterdir()):
        if not engine_dir.is_dir():
            continue
        if engine_dir.name not in ALL_CHART_ENGINES:
            logging.debug("Skipping %s (not in ENGINES registry)", engine_dir.name)
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
    """Annotate bar ends with numeric values (horizontal bars)."""

    for bar, value in zip(bars, values):
        if value is None:
            continue
        width = bar.get_width()
        ax.annotate(
            f"{value:.3f}",
            xy=(width, bar.get_y() + bar.get_height() / 2),
            xytext=(4, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=13,
        )


def _ensure_min_bar_width(bars, values: Sequence[Optional[float]]) -> None:
    """Ensure visible bars even when the underlying value is zero."""

    for bar, value in zip(bars, values):
        if value is None:
            continue
        if bar.get_width() <= 0:
            bar.set_width(MIN_BAR_WIDTH)


def _plot_single_metric(
    ax,
    engines: List[EngineMetrics],
    values: List[Optional[float]],
    title: str,
) -> None:
    """Plot a horizontal bar chart for one metric (best at top)."""

    sortable = list(zip(engines, values))
    sortable.sort(key=lambda item: (item[1] is None, -(item[1] or 0.0)))
    sorted_engines = [engine for engine, _ in sortable]
    sorted_values = [value for _, value in sortable]

    labels = [engine.label for engine in sorted_engines]
    clean_values = [value or 0.0 for value in sorted_values]
    colors = [WINNER_COLOR if i == 0 else OTHER_COLOR for i in range(len(labels))]
    bars = ax.barh(labels, clean_values, color=colors)
    _ensure_min_bar_width(bars, sorted_values)
    _add_value_labels(ax, bars, sorted_values)
    ax.set_xlim(0, 1.15)
    ax.set_title(title, fontsize=14) if title else None
    ax.set_xlabel("Score", fontsize=15)
    ax.invert_yaxis()
    ax.tick_params(axis="y", labelsize=14)


def _plot_grouped_metric(
    ax,
    engines: List[EngineMetrics],
    primary: List[Optional[float]],
    secondary: List[Optional[float]],
    title: str,
    primary_label: str,
    secondary_label: str,
) -> None:
    """Plot grouped horizontal bars for a pair of related metrics (e.g. TEDS/TEDS-S)."""

    combined = list(zip(engines, primary, secondary))
    combined.sort(key=lambda item: (item[1] is None, -(item[1] or 0.0)))
    sorted_engines = [engine for engine, _, _ in combined]
    sorted_primary = [value for _, value, _ in combined]
    sorted_secondary = [value for _, _, value in combined]

    labels = [engine.label for engine in sorted_engines]
    index = range(len(labels))
    height = 0.35

    primary_values = [value or 0.0 for value in sorted_primary]
    secondary_values = [value or 0.0 for value in sorted_secondary]

    bars1 = ax.barh(
        [i - height / 2 for i in index],
        primary_values,
        height,
        label=primary_label,
        color="#59A14F",
    )
    bars2 = ax.barh(
        [i + height / 2 for i in index],
        secondary_values,
        height,
        label=secondary_label,
        color="#E15759",
    )

    _ensure_min_bar_width(bars1, sorted_primary)
    _ensure_min_bar_width(bars2, sorted_secondary)

    _add_value_labels(ax, bars1, sorted_primary)
    _add_value_labels(ax, bars2, sorted_secondary)

    ax.set_xlim(0, 1.15)
    ax.set_title(title, fontsize=14)
    ax.set_xlabel("Score", fontsize=11)
    ax.set_yticks(list(index))
    ax.set_yticklabels(labels, fontsize=10)
    ax.invert_yaxis()
    ax.legend(fontsize=10)


def _plot_time_metric(
    ax,
    engines: List[EngineMetrics],
    values: List[Optional[float]],
) -> None:
    """Plot extraction time per page as horizontal bars (fastest at top)."""

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
    clean_values = [max(value or 0.001, 0.001) for value in sorted_values]
    colors = [TIME_WINNER_COLOR if i == 0 else TIME_OTHER_COLOR for i in range(len(labels))]
    bars = ax.barh(labels, clean_values, color=colors)
    _add_value_labels(ax, bars, sorted_values)
    ax.set_xscale("log")
    ax.set_xlabel("Seconds (log scale)", fontsize=15)
    ax.invert_yaxis()
    ax.tick_params(axis="y", labelsize=14)


def _save_individual_chart(
    plotter: Callable[..., None],
    plot_args: Sequence[object],
    title: str,
    output_path: Path,
    num_engines: int = 7,
) -> None:
    """Render and persist a single chart using an existing plotting helper."""

    fig_height = max(5, num_engines * 0.75 + 2.5)
    fig, ax = plt.subplots(figsize=(8, fig_height), constrained_layout=True)
    plotter(ax, *plot_args)
    ax.set_xlabel(ax.get_xlabel(), fontsize=15)
    ax.tick_params(axis="y", labelsize=14)
    ax.tick_params(axis="x", labelsize=12)
    fig.get_layout_engine().set(rect=(0, 0, 1, 0.91))
    fig.suptitle(title, fontsize=24, y=0.998)
    fig.text(
        0.5, 0.955,
        "200 pages \u00b7 Apple M4 \u00b7 32GB",
        ha="center", va="top", fontsize=15, color="gray",
        transform=fig.transFigure,
    )
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    logging.info("Saved individual chart to %s", output_path)


def _save_grouped_quality_chart(
    engines: List[EngineMetrics],
    nid_values: List[Optional[float]],
    teds_values: List[Optional[float]],
    mhs_values: List[Optional[float]],
    output_path: Path,
) -> None:
    """Three-column horizontal bar chart: NID | TEDS | MHS."""

    num_engines = len(engines)
    fig_h = max(5, num_engines * 0.75 + 2.5)
    fig, (ax_nid, ax_teds, ax_mhs) = plt.subplots(
        1, 3, figsize=(24, fig_h), constrained_layout=True,
    )

    metrics = [
        (ax_nid, nid_values, "Reading Order (NID)"),
        (ax_teds, teds_values, "Table Structure (TEDS)"),
        (ax_mhs, mhs_values, "Heading Hierarchy (MHS)"),
    ]

    for ax, values, title in metrics:
        sortable = list(zip(engines, values))
        sortable.sort(key=lambda item: (item[1] is None, -(item[1] or 0.0)))
        sorted_engines = [e for e, _ in sortable]
        sorted_values = [v for _, v in sortable]

        labels = [e.label for e in sorted_engines]
        clean_values = [v or 0.0 for v in sorted_values]
        colors = [WINNER_COLOR if i == 0 else OTHER_COLOR for i in range(len(labels))]
        bars = ax.barh(labels, clean_values, color=colors)
        _ensure_min_bar_width(bars, sorted_values)
        _add_value_labels(ax, bars, sorted_values)
        ax.set_xlim(0, 1.15)
        ax.set_title(title, fontsize=14)
        ax.set_xlabel("Score", fontsize=15)
        ax.invert_yaxis()
        ax.tick_params(axis="y", labelsize=14)
        ax.tick_params(axis="x", labelsize=12)

    fig.get_layout_engine().set(rect=(0, 0, 1, 0.91))
    fig.suptitle("Structure Quality by Metric", fontsize=24, y=0.998)
    fig.text(0.5, 0.955, "200 pages \u00b7 Apple M4 \u00b7 32GB", ha="center", va="top", fontsize=15, color="gray", transform=fig.transFigure)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    logging.info("Saved quality chart to %s", output_path)


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
    num_engines = len(engines)

    overall_values = [engine.overall for engine in engines]
    nid_values = [engine.nid for engine in engines]
    teds_values = [engine.teds for engine in engines]
    mhs_values = [engine.mhs for engine in engines]
    elapsed_values = [engine.elapsed_per_page for engine in engines]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = "".join(output_path.suffixes) or ".png"
    stem = output_path.stem

    # --- Chart 1: Overall accuracy ---
    overall_path = output_path.parent / f"{stem}_overall{suffix}"
    _save_individual_chart(
        _plot_single_metric,
        (engines, overall_values, ""),
        "Extraction Accuracy",
        overall_path,
        num_engines=num_engines,
    )
    logging.info("Saved overall chart to %s", overall_path)

    # --- Chart 2: Grouped NID / TEDS / MHS ---
    _save_grouped_quality_chart(
        engines, nid_values, teds_values, mhs_values,
        output_path.parent / f"{stem}_quality{suffix}",
    )

    # --- Composite: Overall | Speed ---
    fig_h = max(5, num_engines * 0.75 + 2.5)
    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(16, fig_h), constrained_layout=True)
    _plot_single_metric(ax_left, engines, overall_values, "Extraction Accuracy")
    _plot_time_metric(ax_right, engines, elapsed_values)
    ax_right.set_title("Extraction Time Per Page", fontsize=14)
    fig.get_layout_engine().set(rect=(0, 0, 1, 0.91))
    fig.suptitle("PDF Document Structure Benchmark", fontsize=24, y=0.998)
    fig.text(0.5, 0.955, "200 pages \u00b7 Apple M4 \u00b7 32GB", ha="center", va="top", fontsize=15, color="gray", transform=fig.transFigure)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    logging.info("Saved composite chart to %s", output_path)

    logging.info("Saved benchmark charts")

    # Individual metric charts
    chart_specs: List[Tuple[str, str, Callable[..., None], Tuple[object, ...]]] = [
        (
            "reading-order",
            "Reading Order (NID)",
            _plot_single_metric,
            (engines, nid_values, ""),
        ),
        (
            "table-structure",
            "Table Structure (TEDS)",
            _plot_single_metric,
            (engines, teds_values, ""),
        ),
        (
            "heading-level",
            "Heading Level (MHS)",
            _plot_single_metric,
            (engines, mhs_values, ""),
        ),
        (
            "extraction-time",
            "Extraction Time Per Page",
            _plot_time_metric,
            (engines, elapsed_values),
        ),
    ]

    for suffix_name, title, plotter, plot_args in chart_specs:
        individual_path = output_path.parent / f"{stem}_{suffix_name}{suffix}"
        _save_individual_chart(plotter, plot_args, title, individual_path, num_engines=num_engines)

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
