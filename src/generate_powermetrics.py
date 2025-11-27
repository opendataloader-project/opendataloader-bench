"""Aggregate powermetrics logs and emit per-engine powermetrics JSON files.

This script scans powermetrics.txt files produced by ``powermetrics.sh``,
computes the mean CPU/GPU/ANE/combined power (in mW) and total energy (in J),
and writes the values to ``powermetrics.json`` files under ``prediction/<engine>``.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from collections import defaultdict
from pathlib import Path
from statistics import fmean
from typing import Dict, Iterable, List, Optional

CPU_RE = re.compile(r"CPU Power:\s*(\d+)\s*mW", re.IGNORECASE)
GPU_RE = re.compile(r"GPU Power:\s*(\d+)\s*mW", re.IGNORECASE)
ANE_RE = re.compile(r"ANE Power:\s*(\d+)\s*mW", re.IGNORECASE)
COMBINED_RE = re.compile(r"Combined Power.*?:\s*(\d+)\s*mW", re.IGNORECASE)
ELAPSED_MS_RE = re.compile(r"\(([\d.]+)\s*ms elapsed\)", re.IGNORECASE)

DEFAULT_SAMPLE_INTERVAL_MS = 1000.0


def _mean(values: Iterable[float]) -> Optional[float]:
    values = list(values)
    return fmean(values) if values else None


def parse_powermetrics(log_path: Path) -> Dict[str, float]:
    """Return average power (mW) and total energy (J) from a powermetrics log."""

    if not log_path.is_file():
        raise FileNotFoundError(f"Missing powermetrics log: {log_path}")

    samples: List[Dict[str, float]] = []
    current_sample: Dict[str, float] = {}
    pending_elapsed_ms: Optional[float] = None

    def flush_current():
        nonlocal current_sample
        if current_sample:
            samples.append(current_sample)
            current_sample = {}

    with log_path.open(encoding="utf-8", errors="ignore") as f:
        for line in f:
            elapsed_match = ELAPSED_MS_RE.search(line)
            if elapsed_match:
                pending_elapsed_ms = float(elapsed_match.group(1))
                continue

            cpu_match = CPU_RE.search(line)
            if cpu_match:
                flush_current()
                if pending_elapsed_ms is not None:
                    current_sample["elapsed_ms"] = pending_elapsed_ms
                    pending_elapsed_ms = None
                current_sample["cpu_mw"] = float(cpu_match.group(1))
                continue

            if "gpu_mw" not in current_sample:
                gpu_match = GPU_RE.search(line)
                if gpu_match:
                    current_sample["gpu_mw"] = float(gpu_match.group(1))
                    continue

            ane_match = ANE_RE.search(line)
            if ane_match and "ane_mw" not in current_sample:
                current_sample["ane_mw"] = float(ane_match.group(1))
                continue

            combined_match = COMBINED_RE.search(line)
            if combined_match and "combined_mw" not in current_sample:
                current_sample["combined_mw"] = float(combined_match.group(1))

    flush_current()

    if not samples:
        raise ValueError(f"No power samples found in {log_path}")

    averages: Dict[str, float] = {}
    energy_totals_j: Dict[str, float] = defaultdict(float)
    total_elapsed_seconds = 0.0
    metric_map = {
        "cpu_mw": ("avg_cpu_power_mw", "total_cpu_energy_j"),
        "gpu_mw": ("avg_gpu_power_mw", "total_gpu_energy_j"),
        "ane_mw": ("avg_ane_power_mw", "total_ane_energy_j"),
        "combined_mw": ("avg_combined_power_mw", "total_combined_energy_j"),
    }

    for key, output_keys in metric_map.items():
        values = [sample[key] for sample in samples if key in sample]
        mean_value = _mean(values)
        if mean_value is not None:
            averages[output_keys[0]] = round(mean_value, 2)

    for sample in samples:
        elapsed_ms = sample.get("elapsed_ms", DEFAULT_SAMPLE_INTERVAL_MS)
        elapsed_seconds = elapsed_ms / 1000.0
        total_elapsed_seconds += elapsed_seconds
        for key, (_, energy_key) in metric_map.items():
            if key in sample:
                # mW -> W, then multiply by seconds to get Joules.
                energy_totals_j[energy_key] += sample[key] * elapsed_seconds / 1000.0

    for energy_key, energy_value in energy_totals_j.items():
        averages[energy_key] = round(energy_value, 3)

    averages["power_sample_count"] = len(samples)
    averages["total_elapsed_seconds"] = round(total_elapsed_seconds, 3)
    return averages


def write_powermetrics(powermetrics_path: Path, power_data: Dict[str, float]) -> None:
    """Write ``power_data`` into a powermetrics.json file."""

    with powermetrics_path.open("w", encoding="utf-8") as f:
        json.dump(power_data, f, indent=4)
        f.write("\n")


def process_engine(engine_dir: Path) -> Optional[Dict[str, float]]:
    """Parse powermetrics for a single engine directory."""

    log_path = engine_dir / "powermetrics.txt"
    powermetrics_path = engine_dir / "powermetrics.json"

    if not log_path.is_file():
        logging.warning("Skipping %s (missing powermetrics.txt)", engine_dir.name)
        return None

    power_data = parse_powermetrics(log_path)
    write_powermetrics(powermetrics_path, power_data)
    logging.info(
        "Wrote %s (samples=%d)",
        powermetrics_path,
        power_data.get("power_sample_count", 0),
    )
    return power_data


def find_engines(prediction_root: Path, engines: Optional[List[str]]) -> List[Path]:
    """Return prediction/<engine> directories that should be processed."""

    if engines:
        return [prediction_root / engine for engine in engines]
    return [
        path
        for path in prediction_root.iterdir()
        if path.is_dir() and (path / "powermetrics.txt").is_file()
    ]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute power and total energy from powermetrics logs and write powermetrics.json files."
    )
    parser.add_argument(
        "--prediction-root",
        type=Path,
        default=Path("prediction"),
        help="Root directory containing per-engine folders (default: prediction)",
    )
    parser.add_argument(
        "--engines",
        nargs="*",
        help="Engine names to process; defaults to every engine with powermetrics.txt",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (e.g. INFO, DEBUG)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    prediction_root: Path = args.prediction_root.resolve()
    engine_dirs = find_engines(prediction_root, args.engines)
    if not engine_dirs:
        raise SystemExit("No engines found to process.")

    for engine_dir in engine_dirs:
        process_engine(engine_dir.resolve())


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
