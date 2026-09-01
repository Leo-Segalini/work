"""Orchestration brief 2 — exécution rejouable."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .augmentation import AUGMENTATION_META, augment_noise, augment_time_shift
from .capacity import analyse_capacity
from .detection import detect_control_batch
from .generation import (
    compare_real_vs_synthetic,
    generate_marginal,
    generate_smote,
    pick_site_ouest_equipment,
)
from .laplace import laplace_study

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parents[1]


def run_detector(csv_path: Path) -> dict:
    cmd = [
        sys.executable,
        str(REPO / "tools" / "verify_synthetic.py"),
        "--input",
        str(csv_path),
        "--json",
    ]
    out = subprocess.check_output(cmd, text=True)
    return json.loads(out)


def run_brief2(
    processed_dir: Path,
    output_dir: Path,
    data_dir: Path | None = None,
    seed: int = 42,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    data_root = data_dir or (REPO / "data_pack" / "2026-S1")
    processed_dir = processed_dir.resolve()

    sensors = pd.read_csv(processed_dir / "sensor_readings.csv")
    sample_series = (
        sensors.groupby(["equipment_id", "sensor_name"], observed=True)
        .head(48)
        .reset_index(drop=True)
    )

    # 1. Capacité
    capacity = analyse_capacity(data_root, processed_dir)
    (output_dir / "capacity_report.json").write_text(
        json.dumps(capacity, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # 2. Augmentation
    aug_noise = augment_noise(sample_series, seed=seed)
    aug_shift = augment_time_shift(sample_series.head(200), seed=seed)
    aug_noise.to_csv(output_dir / "augmented_noise.csv", index=False)
    aug_shift.to_csv(output_dir / "augmented_shift.csv", index=False)

    # 3. Génération SITE-OUEST
    targets = pick_site_ouest_equipment(processed_dir, max_n=3)
    gen_marg = generate_marginal(sensors, targets, seed=seed)
    gen_smote = generate_smote(sensors, targets, n_rows=120, seed=seed)
    synthetic = pd.concat([gen_marg, gen_smote], ignore_index=True)
    synthetic.to_csv(output_dir / "generated_site_ouest.csv", index=False)
    comparison = compare_real_vs_synthetic(sensors, synthetic)
    comparison["targets"] = targets

    # 4. Confrontation détecteur — deux états générateur
    journal = []
    raw_path = output_dir / "generated_site_ouest_v1.csv"
    synthetic.to_csv(raw_path, index=False)
    v0 = run_detector(raw_path)
    journal.append({"step": "gen_v1_raw", "hypothesis": "premier générateur SITE-OUEST", "report": v0})

    # version corrigée : clip valeurs dans plages
    fixed = synthetic.copy()
    from .detection import SENSOR_RANGE

    def clip_row(r):
        lo, hi = SENSOR_RANGE.get(r["sensor_name"], (None, None))
        if lo is not None:
            r["value"] = round(min(hi, max(lo, float(r["value"]))), 2)
        return r

    fixed = fixed.apply(clip_row, axis=1)
    fixed_path = output_dir / "generated_site_ouest_v2.csv"
    fixed.to_csv(fixed_path, index=False)
    v1 = run_detector(fixed_path)
    journal.append(
        {
            "step": "gen_v2_clipped",
            "hypothesis": "clip plages physiques après signalement R-RANGE",
            "report": v1,
        }
    )
    (output_dir / "detector_journal.json").write_text(
        json.dumps(journal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # Détection lot de contrôle
    verdicts = detect_control_batch(
        data_root / "sensors_control" / "control_batch.csv",
        processed_dir / "equipment.csv",
        processed_dir / "events.csv",
    )
    verdicts.to_csv(output_dir / "verdicts_control_batch.csv", index=False)
    verdict_counts = verdicts["verdict"].value_counts().to_dict()
    rule_counts = verdicts.groupby("rule_id").size().to_dict()

    # 5. Laplace — agrégat SITE-OUEST (2 équipements → non publiable)
    site_ouest_n = int(
        pd.read_csv(processed_dir / "equipment.csv")
        .loc[lambda f: f.site_id == "SITE-OUEST", "equipment_id"]
        .nunique()
    )
    laplace = laplace_study(true_count=site_ouest_n, sensitivity=1, epsilons=[0.1, 1.0, 10.0], seed=seed)
    (output_dir / "laplace_results.json").write_text(
        json.dumps(laplace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # 6. Jeu transmission M4
    m4_dir = output_dir / "transmission_m4"
    m4_dir.mkdir(exist_ok=True)
    real_out = sensors.copy()
    real_out["provenance"] = "réelle"
    real_out["procedure_id"] = ""
    # transmettre réel + petite part synthétique bornée (SITE-OUEST seulement)
    syn_out = fixed.head(200)  # échantillon, pas tout le synthétique
    transmission = pd.concat([real_out, syn_out], ignore_index=True)
    transmission.to_csv(m4_dir / "sensor_readings_m4.csv", index=False)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "capacity": capacity,
        "augmentation_meta": AUGMENTATION_META,
        "generation": {
            "site_ouest_targets": targets,
            "marginal_rows": len(gen_marg),
            "smote_rows": len(gen_smote),
            "comparison": comparison,
        },
        "detector": {"v1": v0["flagged_rows_total"], "v2": v1["flagged_rows_total"]},
        "verdicts": {"by_verdict": verdict_counts, "by_rule": rule_counts},
        "laplace": laplace,
        "transmission_m4": {
            "path": str(m4_dir / "sensor_readings_m4.csv"),
            "real_rows": len(real_out),
            "synthetic_rows": len(syn_out),
            "decision": "transmission sous conditions",
            "conditions": [
                "provenance obligatoire sur chaque ligne",
                "synthétique limité à SITE-OUEST et documenté (GEN-MARG/SMOTE)",
                "pas de conclusion parc entier",
                "retirer synthétique si modèle M4 sensible aux corrélations inter-sources",
            ],
        },
        "biases": [
            {
                "bias": "couverture instrumentale",
                "chiffre": f"{capacity['coverage_rate']*100:.1f}% du parc",
                "attenuation": "génération SITE-OUEST",
                "residuel": "biais de sélection persistant",
                "amplifie_par_generation": False,
            },
            {
                "bias": "sévérité événements",
                "chiffre": f"ratio max/min sévérité = {capacity['severity_imbalance_ratio']}",
                "attenuation": "sur-échantillonnage (non retenu ici)",
                "residuel": "événements rares sous-représentés",
                "amplifie_par_generation": True,
            },
            {
                "bias": "historique maintenance",
                "chiffre": "parc M2 déjà filtré (quarantaine)",
                "attenuation": "documenter périmètre",
                "residuel": "activité passée non représentative",
                "amplifie_par_generation": False,
            },
        ],
    }
    (output_dir / "brief2_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary
