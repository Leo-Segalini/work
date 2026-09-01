#!/usr/bin/env python3
"""Qualifie la livraison candidate M2."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.candidate_qualification import qualify_candidate  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Qualifie la livraison candidate M2.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Code de sortie 1 si décision REJECTED (démonstration CI).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "output/candidate_qualification",
        help="Répertoire de sortie des rapports.",
    )
    args = parser.parse_args()

    data = ROOT / "../../data_pack/2026-S1"
    candidate = data / "m2_candidate_release"
    summary = qualify_candidate(data.resolve(), candidate.resolve(), args.output.resolve())
    print(
        json.dumps(
            {
                "decision": summary["decision"],
                "blocking": summary["blocking"],
                "output": str(args.output.resolve()),
            },
            indent=2,
        )
    )
    if args.strict and summary["decision"] == "REJECTED":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
