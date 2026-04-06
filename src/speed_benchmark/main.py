# src/speed_benchmark/main.py
import argparse
import sys
from pathlib import Path

from .parsers import ALL_PARSERS
from .runner import run_benchmark
from .report import save_json, save_chart, update_readme


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="benchmark",
        description="PDF parser speed benchmark — measures latency and peak memory.",
    )
    parser.add_argument(
        "--pdf",
        default="speed_benchmark_data/GPO-911REPORT.pdf",
        help="Path to PDF file (default: speed_benchmark_data/GPO-911REPORT.pdf)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=10,
        help="Number of timed iterations per parser (default: 10)",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=1,
        help="Number of warmup runs before timing (default: 1)",
    )
    parser.add_argument(
        "--parsers",
        help="Comma-separated list of parser names to run (default: all).",
    )
    parser.add_argument(
        "--json-out",
        default="speed_results/latest.json",
        help="Output path for JSON results (default: speed_results/latest.json)",
    )
    parser.add_argument(
        "--chart-out",
        default="charts/benchmark_speed.png",
        help="Output path for chart PNG (default: charts/benchmark_speed.png)",
    )
    parser.add_argument(
        "--readme",
        default="README.md",
        help="README path to update (default: README.md)",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    parsers = ALL_PARSERS
    if args.parsers:
        names = {n.strip() for n in args.parsers.split(",")}
        parsers = [p for p in ALL_PARSERS if p.name in names]
        if not parsers:
            print(f"Error: no parsers matched '{args.parsers}'", file=sys.stderr)
            sys.exit(1)

    print(f"Benchmarking {len(parsers)} parser(s) against {pdf_path}")
    print(f"  iterations={args.iterations}, warmup={args.warmup}\n")

    results = run_benchmark(
        parsers,
        str(pdf_path),
        iterations=args.iterations,
        warmup_runs=args.warmup,
    )

    print("\nSaving results...")
    save_json(results, args.json_out)
    save_chart(results, args.chart_out)
    update_readme(results, args.readme)

    print("\nDone. Summary:")
    for r in results:
        if r.status == "ok":
            print(f"  {r.name}: {r.avg_latency:.3f}s avg, {r.avg_peak_memory_mb:.1f}MB peak")
        else:
            print(f"  {r.name}: {r.status}" + (f" — {r.error}" if r.error else ""))


if __name__ == "__main__":
    main()
