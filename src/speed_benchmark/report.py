# src/speed_benchmark/report.py
import json
import re
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .runner import ParserResult


def results_to_dict(results: list[ParserResult]) -> dict:
    return {
        "results": [
            {
                "name": r.name,
                "status": r.status,
                "error": r.error,
                "avg_latency": r.avg_latency,
                "median_latency": r.median_latency,
                "stddev_latency": r.stddev_latency,
                "min_latency": r.min_latency,
                "max_latency": r.max_latency,
                "avg_peak_memory_mb": r.avg_peak_memory_mb,
                "latencies": r.latencies,
                "peak_memories_mb": r.peak_memories_mb,
            }
            for r in results
        ]
    }


def save_json(results: list[ParserResult], path: str = "speed_results/latest.json") -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(results_to_dict(results), f, indent=2)
    print(f"Saved: {path}")


def save_chart(results: list[ParserResult], path: str = "charts/benchmark_speed.png") -> None:
    ok = [r for r in results if r.status == "ok"]
    ok_sorted = sorted(ok, key=lambda r: r.avg_latency or float("inf"))

    names = [r.name for r in ok_sorted]
    latencies = [r.avg_latency or 0 for r in ok_sorted]
    memories = [r.avg_peak_memory_mb or 0 for r in ok_sorted]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, max(4, len(names) * 0.7 + 2)))
    fig.suptitle("PDF Parser Speed Benchmark\nGPO-911REPORT.pdf · 585 pages · OCR Disabled · Apple M4 · 32GB · macOS 26.3", fontsize=12)

    colors = plt.cm.RdYlGn_r([i / max(len(names) - 1, 1) for i in range(len(names))])

    bars1 = ax1.barh(names, latencies, color=colors)
    ax1.set_xlabel("Avg Latency (s) — log scale")
    ax1.set_title("Latency")
    ax1.set_xscale("log")
    ax1.invert_yaxis()
    for bar, val in zip(bars1, latencies):
        ax1.text(bar.get_width() * 1.05, bar.get_y() + bar.get_height() / 2,
                 f"{val:.2f}s", va="center", fontsize=9)

    bars2 = ax2.barh(names, memories, color=colors)
    ax2.set_xlabel("Avg Peak Memory (MB) — log scale")
    ax2.set_title("Peak Memory")
    ax2.set_xscale("log")
    ax2.invert_yaxis()
    for bar, val in zip(bars2, memories):
        ax2.text(bar.get_width() * 1.05, bar.get_y() + bar.get_height() / 2,
                 f"{val:.1f}MB", va="center", fontsize=9)

    plt.tight_layout()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {path}")


def _fmt(val: Optional[float], decimals: int = 3) -> str:
    return f"{val:.{decimals}f}" if val is not None else "N/A"


def _build_markdown_block(results: list[ParserResult]) -> str:
    lines = [
        "![Benchmark Chart](charts/benchmark_speed.png)",
        "",
        "| Parser | Status | Avg (s) | Median (s) | Stddev | Min (s) | Max (s) | Peak Mem (MB) |",
        "|--------|--------|---------|------------|--------|---------|---------|---------------|",
    ]
    ok = sorted([r for r in results if r.status == "ok"], key=lambda r: r.avg_latency or float("inf"))
    other = [r for r in results if r.status != "ok"]
    for r in ok + other:
        lines.append(
            f"| {r.name} | {r.status} | {_fmt(r.avg_latency)} | {_fmt(r.median_latency)} | "
            f"{_fmt(r.stddev_latency)} | {_fmt(r.min_latency)} | {_fmt(r.max_latency)} | "
            f"{_fmt(r.avg_peak_memory_mb, 1)} |"
        )
    return "\n".join(lines)


def update_readme(results: list[ParserResult], readme_path: str = "README.md") -> None:
    path = Path(readme_path)
    content = path.read_text() if path.exists() else ""

    block = _build_markdown_block(results)
    replacement = f"<!-- BENCHMARK_START -->\n{block}\n<!-- BENCHMARK_END -->"

    pattern = r"<!-- BENCHMARK_START -->.*?<!-- BENCHMARK_END -->"
    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    else:
        new_content = content + "\n" + replacement + "\n"

    path.write_text(new_content)
    print(f"Updated: {readme_path}")
