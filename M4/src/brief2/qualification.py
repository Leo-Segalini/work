"""Brief 2 — qualification des lots inédits (test scellé)."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from ..io_contracts import load_manifest, load_questions


def qualify_sensor_test(test_path: Path) -> dict:
    with test_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    windows = {r["window_id"] for r in rows}
    sensors = Counter(r["sensor_name"] for r in rows)
    equipment = Counter(r["equipment_id"] for r in rows)
    return {
        "rows": len(rows),
        "windows": len(windows),
        "sensors": dict(sensors),
        "unique_equipment": len(equipment),
        "has_provenance_label": "provenance" in (rows[0] if rows else {}),
        "note": "Lot sans étiquette — distribution descriptive seulement, pas de réglage de seuils.",
    }


def qualify_rag_test(questions_path: Path, manifest_path: Path, documents_dir: Path) -> dict:
    questions = [q for q in load_questions(questions_path) if q["split"] == "test"]
    manifest = load_manifest(manifest_path, documents_dir)
    roles = Counter(q["role"] for q in questions)
    risks = Counter(tag for q in questions for tag in q.get("risk_tags", []))
    return {
        "questions": len(questions),
        "roles": dict(roles),
        "risk_tags": dict(risks),
        "labels_sealed": all(q["label_visibility"] == "sealed" for q in questions),
        "corpus_documents": len(manifest),
        "non_answerable_expected": "missing_evidence, restricted_data, scope (à valider oracle)",
    }


def qualify_new_lot(data_dir: Path) -> dict:
    return {
        "sensor_test": qualify_sensor_test(data_dir / "model_eval/sensor_test.csv"),
        "rag_test": qualify_rag_test(
            data_dir / "rag_eval/questions.jsonl",
            data_dir / "knowledge/manifest.csv",
            data_dir / "knowledge/documents",
        ),
        "decision_admission": "utiliser pour évaluation gelée — pas pour calibration",
    }
