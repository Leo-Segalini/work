#!/usr/bin/env python3
"""Lanceur DiagOps M3."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
os.environ.setdefault("PYTHONPATH", str(ROOT))
PYTHON = sys.executable
DATA = ROOT / "../../data_pack/2026-S1"
M2 = ROOT / "../M2/output/processed"

ACTIONS = [
    ("1", "Audit capteurs (avant intégration)", "audit"),
    ("2", "Pipeline multi-source complète", "pipeline"),
    ("3", "Afficher validation_report.json", "report"),
    ("4", "Tests", "tests"),
    ("5", "Notebook multisource", "nb_ms"),
    ("6", "Workflow DB online (migrations + import)", "db"),
    ("7", "Brief 2 — capacité, génération, détection", "brief2"),
    ("8", "Interface explorateur (Streamlit)", "ui"),
    ("0", "Quitter", "quit"),
]


def run(cmd: str) -> int:
    print(f"\n$ {cmd}\n")
    return subprocess.run(cmd, shell=True, cwd=ROOT).returncode


def main() -> int:
    while True:
        print("\n=== Lanceur DiagOps M3 ===")
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
        if kind == "audit":
            run(f"{PYTHON} scripts/audit_sensors.py --output ./output/audit")
        elif kind == "pipeline":
            m2_flag = f"--m2-processed {M2}" if M2.is_dir() else ""
            run(
                f"{PYTHON} -m src.data_pipeline --input {DATA.resolve()} "
                f"--output ./output {m2_flag}"
            )
        elif kind == "report":
            p = ROOT / "output" / "validation_report.json"
            print(p.read_text(encoding="utf-8") if p.exists() else "Lancez [2].")
        elif kind == "tests":
            run(f"{PYTHON} -m pytest -q")
        elif kind == "nb_ms":
            run(f"{PYTHON} -m jupyter lab notebooks/notebook_multisource_m3.ipynb")
        elif kind == "db":
            run(f"{PYTHON} scripts/db_workflow.py --reset --processed {ROOT / 'output/processed'}")
        elif kind == "brief2":
            run(
                f"{PYTHON} scripts/brief2_run.py "
                f"--processed {ROOT / 'output/processed'} --output {ROOT / 'output/brief2'}"
            )
        elif kind == "ui":
            run(f"{PYTHON} -m streamlit run ui/explorer_app.py --server.headless true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
