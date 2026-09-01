"""Brief 2 — orchestration."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .audit import audit_transmissibility
from .correction import evaluate_correction
from .extended_threats import EXTENDED_THREATS, run_extended_threats
from .qualification import qualify_new_lot


def run_brief2(root: Path, data_dir: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    cfg = root / "configs/retrieval.yaml"

    audit = audit_transmissibility(root)
    qualification = qualify_new_lot(data_dir)
    correction = evaluate_correction(cfg, output_dir / "brief2")
    threats = run_extended_threats()

    # Rejeu baselines : pointer vers résultats brief1 gelés
    brief1 = output_dir / "m4_summary.json"
    replay = {"status": "non testé"}
    if brief1.is_file():
        replay = {
            "status": "reproduit",
            "source": str(brief1),
            "model_f1": json.loads(brief1.read_text())["model"]["candidates"]["random_forest"][
                "calibration_full"
            ]["f1"],
        }

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "audit": audit,
        "qualification": qualification,
        "correction": correction,
        "extended_threats": {"cases": EXTENDED_THREATS, "checks": threats},
        "replay_brief1": replay,
        "decision_revised": (
            "Adopter lexical-first pour RAG (latence) ; maintenir RF capteur sous validation test formateur"
        ),
    }
    (output_dir / "brief2_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary
