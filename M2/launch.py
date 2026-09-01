#!/usr/bin/env python3
"""Lanceur DiagOps M2 — audit, PII, notebooks.

Depuis work/M2 :

    source .venv/bin/activate
    python3 launch.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
os.environ.setdefault("PYTHONPATH", str(ROOT))
PYTHON = sys.executable

ACTIONS = [
    ("1", "Lancer le pipeline d'audit (qualité + PII)", "run_pipeline"),
    ("2", "Afficher le rapport PII", "show_pii"),
    ("3", "Afficher la décision d'audit", "show_audit"),
    ("4", "Lancer les tests", "tests"),
    ("5", "Ouvrir le notebook d'audit présentiel", "nb_audit"),
    ("6", "Ouvrir le notebook stats online", "nb_stats"),
    ("7", "Réexécuter stats + exporter HTML", "export_stats"),
    ("8", "Afficher le journal de bord", "show_journal"),
    ("9", "Qualifier livraison candidate (aller plus loin)", "candidate"),
    ("0", "Quitter", "quit"),
]


def run(cmd: str) -> int:
    print(f"\n$ {cmd}\n")
    return subprocess.run(cmd, shell=True, cwd=ROOT).returncode


def main() -> int:
    while True:
        print("\n=== Lanceur DiagOps M2 ===")
        print(f"Répertoire: {ROOT}\n")
        for key, title, _ in ACTIONS:
            print(f"  [{key}] {title}")
        choice = input("\nVotre choix: ").strip()
        action = next((a for a in ACTIONS if a[0] == choice), None)
        if not action:
            print("Choix invalide.")
            continue
        kind = action[2]
        if kind == "quit":
            return 0
        if kind == "run_pipeline":
            run(
                f"{PYTHON} -m src.data_pipeline "
                "--input ../../data_pack/2026-S1 --output ./output"
            )
        elif kind == "show_pii":
            path = ROOT / "reports" / "pii_findings.md"
            print(path.read_text(encoding="utf-8") if path.exists() else "Absent — lancez [1].")
        elif kind == "show_audit":
            path = ROOT / "reports" / "audit_report.md"
            print(path.read_text(encoding="utf-8") if path.exists() else "Absent — lancez [1].")
        elif kind == "tests":
            run(f"{PYTHON} -m pytest -q")
        elif kind == "nb_audit":
            run(f"{PYTHON} -m jupyter lab notebooks/notebook_audit_m2.ipynb")
        elif kind == "nb_stats":
            run(f"{PYTHON} -m jupyter lab notebooks/m2_statistiques_atlas.ipynb")
        elif kind == "export_stats":
            run(
                f"{PYTHON} -m jupyter nbconvert --to notebook --execute "
                "notebooks/m2_statistiques_atlas.ipynb --inplace "
                "--ExecutePreprocessor.timeout=180"
            )
            run(
                f"{PYTHON} -m jupyter nbconvert --to html "
                "notebooks/m2_statistiques_atlas.ipynb "
                "--output-dir reports --output m2_statistiques_atlas.html"
            )
            print("→ reports/m2_statistiques_atlas.html")
        elif kind == "show_journal":
            path = ROOT / "journal_bord.md"
            print(path.read_text(encoding="utf-8") if path.exists() else "Absent.")
        elif kind == "candidate":
            run(f"{PYTHON} scripts/qualify_candidate.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
