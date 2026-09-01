"""Brief 2 — audit de transmissibilité du dépôt M4."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def audit_transmissibility(root: Path) -> dict:
    required = [
        "configs/model.yaml",
        "configs/retrieval.yaml",
        "requirements.lock",
        "scripts/run_pipeline.py",
        "src/model_eval.py",
        "src/rag_pipeline.py",
        "src/baseline_m3.py",
        "src/features.py",
        "docs/protocole_evaluation.md",
    ]
    checks = []
    missing = []
    for rel in required:
        p = root / rel
        ok = p.is_file()
        checks.append({"artifact": rel, "present": ok, "sha256": sha256_file(p) if ok else None})
        if not ok:
            missing.append(rel)

    repro = {"status": "non testé", "pytest_exit": None}
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=300,
            env={**os.environ, "PYTHONPATH": str(root)},
        )
        repro = {
            "status": "reproduit" if proc.returncode == 0 else "écart",
            "pytest_exit": proc.returncode,
            "stdout_tail": proc.stdout.strip().splitlines()[-3:],
        }
    except Exception as exc:  # pragma: no cover
        repro = {"status": "bloqué", "error": str(exc)}

    return {
        "artifacts_checked": len(checks),
        "missing": missing,
        "checks": checks,
        "reproduction_pytest": repro,
        "transmissible": not missing and repro["status"] == "reproduit",
        "gaps_before_change": [
            "Oracle test capteur et labels RAG test : formateur uniquement",
            "Lot contradiction brief 2 : canal formateur post-gel",
        ],
    }
