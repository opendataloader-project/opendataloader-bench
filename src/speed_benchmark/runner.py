# src/speed_benchmark/runner.py
import statistics
import time
import tracemalloc
from dataclasses import dataclass, field
from typing import Optional

from .parsers.base import BaseParser


@dataclass
class ParserResult:
    name: str
    status: str  # "ok" | "unavailable" | "error"
    error: Optional[str] = None
    latencies: list[float] = field(default_factory=list)
    peak_memories_mb: list[float] = field(default_factory=list)

    @property
    def avg_latency(self) -> Optional[float]:
        return statistics.mean(self.latencies) if self.latencies else None

    @property
    def median_latency(self) -> Optional[float]:
        return statistics.median(self.latencies) if self.latencies else None

    @property
    def stddev_latency(self) -> Optional[float]:
        return statistics.stdev(self.latencies) if len(self.latencies) > 1 else 0.0

    @property
    def min_latency(self) -> Optional[float]:
        return min(self.latencies) if self.latencies else None

    @property
    def max_latency(self) -> Optional[float]:
        return max(self.latencies) if self.latencies else None

    @property
    def avg_peak_memory_mb(self) -> Optional[float]:
        return statistics.mean(self.peak_memories_mb) if self.peak_memories_mb else None


def run_benchmark(
    parsers: list[BaseParser],
    pdf_path: str,
    iterations: int = 10,
    warmup_runs: int = 1,
) -> list[ParserResult]:
    results = []
    for parser in parsers:
        print(f"  [{parser.name}] checking availability...", flush=True)
        if not parser.is_available():
            print(f"  [{parser.name}] UNAVAILABLE — skipping", flush=True)
            results.append(ParserResult(name=parser.name, status="unavailable"))
            continue

        print(f"  [{parser.name}] warming up ({warmup_runs} run(s))...", flush=True)
        for _ in range(warmup_runs):
            try:
                parser.parse(pdf_path)
            except Exception:
                pass

        result = ParserResult(name=parser.name, status="ok")
        print(f"  [{parser.name}] running {iterations} iterations...", flush=True)
        for i in range(iterations):
            try:
                tracemalloc.start()
                t0 = time.perf_counter()
                parser.parse(pdf_path)
                latency = time.perf_counter() - t0
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                result.latencies.append(latency)
                result.peak_memories_mb.append(peak / 1024 / 1024)
                print(f"  [{parser.name}] iter {i+1}/{iterations}: {latency:.3f}s", flush=True)
            except Exception as e:
                tracemalloc.stop()
                result.status = "error"
                result.error = str(e)
                print(f"  [{parser.name}] ERROR on iter {i+1}: {e}", flush=True)
                break

        results.append(result)

    return results
