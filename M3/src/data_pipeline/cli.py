"""Pipeline multi-source DiagOps M3.

- Reprend l'état préparé M2 (`m2_for_m3` ou `--m2-processed`)
- Prépare les capteurs avec arbitrage tracé (pas d'intégration silencieuse)
- Produit agrégats + rapprochement mesures ↔ événements
- Quarantaine unifiée + rapport de validation + décision
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import pandas as pd

from contracts.schemas import (
    ALIGN_AFTER_HOURS,
    ALIGN_BEFORE_HOURS,
    align_measures_to_events,
)
from src.data_pipeline.io import (
    file_sha256,
    load_reference,
    load_sources,
    source_checksums,
)
from src.data_pipeline.quarantine import merge_quarantines
from src.data_pipeline.registry_builder import build_registry
from src.data_pipeline.sensors import prepare_sensors
from src.data_pipeline.timeseries import series_overview


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pipeline multi-source DiagOps M3")
    parser.add_argument("--input", type=Path, required=True, help="dossier data_pack période")
    parser.add_argument("--output", type=Path, required=True, help="dossier des sorties")
    parser.add_argument(
        "--m2-processed",
        type=Path,
        default=None,
        help="dossier processed M2 personnel (sinon référence m2_for_m3)",
    )
    return parser


def _copy_m2_tables(src_dir: Path, dest_dir: Path) -> dict[str, int]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        "equipment.csv": "equipment.csv",
        "events.csv": "events.csv",
        "maintenance_history.csv": "maintenance_history.csv",
    }
    counts = {}
    for name, dest_name in mapping.items():
        src = src_dir / name
        if not src.is_file():
            raise FileNotFoundError(f"Table M2 absente : {src}")
        shutil.copy2(src, dest_dir / dest_name)
        counts[name] = sum(1 for _ in src.open(encoding="utf-8")) - 1
    return counts


def _aggregates(sensors: pd.DataFrame) -> pd.DataFrame:
    if sensors.empty:
        return pd.DataFrame(
            columns=[
                "equipment_id",
                "sensor_name",
                "n",
                "completeness",
                "min",
                "max",
                "mean",
                "std",
            ]
        )
    work = sensors.copy()
    work["value"] = pd.to_numeric(work["value"], errors="coerce")
    grouped = work.groupby(["equipment_id", "sensor_name"], observed=True)["value"]
    agg = grouped.agg(["count", "min", "max", "mean", "std"]).reset_index()
    agg = agg.rename(columns={"count": "n"})
    # complétude : part de valeurs non nulles dans le groupe (déjà count)
    totals = work.groupby(["equipment_id", "sensor_name"], observed=True).size().rename("n_total")
    agg = agg.merge(totals, on=["equipment_id", "sensor_name"])
    agg["completeness"] = (agg["n"] / agg["n_total"]).round(4)
    return agg.drop(columns=["n_total"])


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    out = args.output
    for name in ("processed", "aggregates", "alignment", "docs"):
        (out / name).mkdir(parents=True, exist_ok=True)

    sources = load_sources(args.input)
    checksums = source_checksums(args.input)
    reference = load_reference(args.input)

    # --- Point de départ M2 ---
    if args.m2_processed is not None:
        m2_dir = args.m2_processed.resolve()
        m2_source_label = f"personnel:{m2_dir}"
        m2_quarantine = pd.DataFrame()
        q_path = m2_dir.parent / "quarantine.csv"
        if q_path.is_file():
            m2_quarantine = pd.read_csv(q_path)
    else:
        ref_processed = (args.input / "reference_runs" / "m2_for_m3" / "processed").resolve()
        m2_dir = ref_processed
        m2_source_label = "reference:m2_for_m3"
        m2_quarantine = reference["quarantine"]

    m2_counts = _copy_m2_tables(m2_dir, out / "processed")
    equipment = pd.read_csv(out / "processed" / "equipment.csv")
    events = pd.read_csv(out / "processed" / "events.csv")
    known_eq = set(equipment["equipment_id"].astype(str))

    # Non-régression : empreintes des tables M2 reprises
    m2_hashes = {
        name: file_sha256(out / "processed" / name)
        for name in ("equipment.csv", "events.csv", "maintenance_history.csv")
    }

    # --- Capteurs ---
    processed_sensors, sensor_q, sensor_stats = prepare_sensors(
        sources["sensors"], known_equipment_ids=known_eq
    )
    processed_sensors.to_csv(out / "processed" / "sensor_readings.csv", index=False)

    overview = series_overview(processed_sensors) if len(processed_sensors) else pd.DataFrame()
    overview.to_csv(out / "series_overview.csv", index=False)

    aggregates = _aggregates(processed_sensors)
    aggregates.to_csv(out / "aggregates" / "by_equipment_sensor.csv", index=False)

    alignment = align_measures_to_events(
        processed_sensors, events, ALIGN_BEFORE_HOURS, ALIGN_AFTER_HOURS
    )
    alignment.to_csv(out / "alignment" / "measures_events.csv", index=False)

    # Cardinalité rapprochement
    n_meas = len(processed_sensors)
    paired_meas = set(alignment["measurement_id"]) if len(alignment) else set()
    paired_events = set(alignment["event_id"]) if len(alignment) else set()
    align_stats = {
        "before_hours": ALIGN_BEFORE_HOURS,
        "after_hours": ALIGN_AFTER_HOURS,
        "alignment_rows": int(len(alignment)),
        "measures_total": n_meas,
        "measures_paired": int(len(paired_meas)),
        "measures_unpaired": int(n_meas - len(paired_meas)),
        "events_total": int(len(events)),
        "events_with_measures": int(len(paired_events)),
        "events_without_measures": int(len(events) - len(paired_events)),
    }

    quarantine = merge_quarantines(m2_quarantine, sensor_q)
    quarantine.to_csv(out / "quarantine.csv", index=False)

    registry = build_registry()
    registry.to_frame().to_csv(out / "registre_regles.csv", index=False)
    (out / "docs" / "registre_regles.md").write_text(registry.to_markdown(), encoding="utf-8")

    # Couverture
    eq_all = set(equipment["equipment_id"].astype(str))
    eq_inst = set(processed_sensors["equipment_id"].astype(str)) if len(processed_sensors) else set()
    coverage = {
        "equipment_total": len(eq_all),
        "equipment_instrumented": len(eq_inst),
        "coverage_rate": round(len(eq_inst) / len(eq_all), 4) if eq_all else 0.0,
    }

    excluded = sensor_stats["excluded"]
    if excluded > 2000 or coverage["coverage_rate"] < 0.02:
        decision = "non utilisable en l'état"
        reason = "Volume d'exclusions ou couverture instrumentale trop faible."
    elif excluded > 0 or coverage["coverage_rate"] < 0.5:
        decision = "utilisable sous conditions"
        reason = (
            "Capteurs préparés après exclusion des anomalies ; couverture partielle "
            "du parc ; utiliser processed/ + quarantine ; pas de conclusion parc entier."
        )
    else:
        decision = "utilisable"
        reason = "Peu d'exclusions et couverture suffisante pour le périmètre instrumenté."

    report = {
        "status": "completed",
        "m2_source": m2_source_label,
        "sources": {
            name: {"rows": len(frame), "sha256": checksums[name]}
            for name, frame in sources.items()
        },
        "m2_processed_rows": m2_counts,
        "m2_processed_sha256": m2_hashes,
        "sensors": sensor_stats,
        "series": {
            "count": int(len(overview)),
            "equipment_with_measurements": int(
                overview["equipment_id"].nunique() if len(overview) else 0
            ),
        },
        "alignment": align_stats,
        "coverage": coverage,
        "rules": {
            "declared": len(registry.rules),
            "active": len(registry.active()),
            "missing_m2": registry.missing(
                __import__("contracts.schemas", fromlist=["M2_RULE_IDS"]).M2_RULE_IDS
            ),
        },
        "summary": {
            "quarantined_rows": int(len(quarantine)),
            "sensor_excluded": excluded,
            "sensor_kept": sensor_stats["kept"],
        },
        "decision": decision,
        "decision_reason": reason,
        "timezone_hypothesis": "UTC (horodatages naïfs interprétés UTC)",
    }
    (out / "validation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "decision": decision,
        "sensors_kept": sensor_stats["kept"],
        "sensors_excluded": excluded,
        "alignment_rows": align_stats["alignment_rows"],
        "coverage_rate": coverage["coverage_rate"],
    }, ensure_ascii=False, indent=2))
    return 0
