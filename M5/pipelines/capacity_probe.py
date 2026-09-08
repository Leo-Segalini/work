#!/usr/bin/env python3
"""Profil de charge local M5 — endpoints santé uniquement (pas de service externe)."""

from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
from pathlib import Path


def timed_get(url: str, timeout: float) -> tuple[int, float]:
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            response.read()
            status = int(response.status)
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
    except Exception:
        status = 0
    elapsed_ms = (time.perf_counter() - started) * 1000
    return status, elapsed_ms


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((pct / 100) * (len(ordered) - 1)))))
    return ordered[index]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--output", type=Path, default=Path("artifacts/candidates/local/capacity_report.json"))
    args = parser.parse_args()

    endpoints = [
        f"{args.base_url.rstrip('/')}/health/live",
        f"{args.base_url.rstrip('/')}/health/ready",
        f"{args.base_url.rstrip('/')}/version",
        f"{args.base_url.rstrip('/')}/metrics",
    ]
    latencies: list[float] = []
    errors = 0
    started = time.perf_counter()
    for i in range(args.requests):
        url = endpoints[i % len(endpoints)]
        status, elapsed_ms = timed_get(url, args.timeout)
        latencies.append(elapsed_ms)
        if status == 0 or status >= 400:
            errors += 1
    duration_s = max(time.perf_counter() - started, 1e-9)

    report = {
        "profile": "lab_smoke_sequential_v1",
        "base_url": args.base_url,
        "requests": args.requests,
        "duration_s": round(duration_s, 3),
        "throughput_rps": round(args.requests / duration_s, 2),
        "error_count": errors,
        "error_rate": round(errors / args.requests, 4),
        "latency_ms": {
            "p50": round(percentile(latencies, 50), 2),
            "p95": round(percentile(latencies, 95), 2),
            "max": round(max(latencies), 2) if latencies else 0.0,
            "mean": round(statistics.fmean(latencies), 2) if latencies else 0.0,
        },
        "first_saturation_hypothesis": (
            "CPU conteneur API / GIL Python sous charge concurrente réelle ; "
            "ici profil séquentiel labo — saturation non forcée."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
