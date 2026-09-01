#!/usr/bin/env python3
"""Lance le brief 2 M3 (capacité → transmission M4)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.brief2.pipeline import run_brief2  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Brief 2 M3 — capacité et transmission M4")
    parser.add_argument(
        "--processed",
        type=Path,
        default=ROOT / "output" / "processed",
        help="CSV préparés issue du brief 1",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "output" / "brief2",
        help="dossier de sortie brief 2",
    )
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    summary = run_brief2(args.processed, args.output, args.data_dir, seed=args.seed)
    print(json.dumps(
        {
            "decision": summary["transmission_m4"]["decision"],
            "verdicts": summary["verdicts"]["by_verdict"],
            "detector_v1": summary["detector"]["v1"],
            "detector_v2": summary["detector"]["v2"],
            "output": str(args.output.resolve()),
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
