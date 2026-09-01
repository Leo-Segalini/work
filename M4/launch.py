#!/usr/bin/env python3
"""Lanceur DiagOps M4."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
os.environ.setdefault("PYTHONPATH", str(ROOT))
PYTHON = sys.executable
DATA = (ROOT / "../../data_pack/2026-S1").resolve()

ACTIONS = [
    ("1", "Valider contrats (manifeste + questions)", "contracts"),
    ("2", "Pipeline complet (modèle + RAG)", "pipeline"),
    ("3", "Modèle capteur seul", "model"),
    ("4", "Tests pytest", "tests"),
    ("5", "Afficher résumé results/m4_summary.json", "summary"),
    ("6", "Interface explorateur (Streamlit)", "ui"),
    ("7", "Brief 2 — audit, qualification, correction", "brief2"),
    ("8", "Grille reproduction + passage M5", "repro"),
    ("0", "Quitter", "quit"),
]


def run(cmd: str) -> int:
    print(f"\n$ {cmd}\n")
    return subprocess.run(cmd, shell=True, cwd=ROOT).returncode


def main() -> int:
    while True:
        print("\n=== Lanceur DiagOps M4 ===")
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
        if kind == "contracts":
            run(
                f"{PYTHON} -m src.io_contracts "
                f"--manifest {DATA / 'knowledge/manifest.csv'} "
                f"--documents {DATA / 'knowledge/documents'} "
                f"--questions {DATA / 'rag_eval/questions.jsonl'}"
            )
        elif kind == "pipeline":
            run(f"{PYTHON} scripts/run_pipeline.py")
        elif kind == "model":
            run(
                f"{PYTHON} -c \"from pathlib import Path; from src.model_eval import evaluate_models; "
                f"evaluate_models(Path('{DATA}/model_eval/sensor_calibration.csv'), "
                f"Path('{DATA}/model_eval/sensor_test.csv'), Path('results'), Path('configs/model.yaml'))\""
            )
        elif kind == "tests":
            run(f"{PYTHON} -m pytest -q")
        elif kind == "summary":
            p = ROOT / "results/m4_summary.json"
            print(p.read_text(encoding="utf-8") if p.exists() else "Lancez [2].")
        elif kind == "ui":
            run(f"{PYTHON} -m streamlit run ui/explorer_app.py --server.headless true")
        elif kind == "brief2":
            run(f"{PYTHON} scripts/run_brief2.py")
        elif kind == "repro":
            run(f"{PYTHON} scripts/run_reproduction_grille.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
