#!/usr/bin/env python3
"""Brief 2 M4 — audit, qualification, correction, menaces."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.brief2 import run_brief2  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Brief 2 M4")
    parser.add_argument("--data", type=Path, default=ROOT / "../../data_pack/2026-S1")
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    summary = run_brief2(ROOT, args.data.resolve(), args.output.resolve())
    print(json.dumps(
        {
            "transmissible": summary["audit"]["transmissible"],
            "correction": summary["correction"]["change"],
            "latency_before_ms": summary["correction"]["before"]["avg_latency_ms"],
            "latency_after_ms": summary["correction"]["after"]["avg_latency_ms"],
            "decision": summary["decision_revised"],
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
