"""Partie 4 — détection ligne à ligne sur le lot de contrôle."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

EXPECTED_UNIT = {
    "vibration_mm_s": "mm/s",
    "temperature_c": "°C",
    "pressure_bar": "bar",
    "current_a": "A",
    "rpm": "rpm",
}
SENSOR_RANGE = {
    "vibration_mm_s": (0.0, 12.0),
    "temperature_c": (-20.0, 140.0),
    "pressure_bar": (0.0, 25.0),
    "current_a": (0.0, 120.0),
    "rpm": (0.0, 3000.0),
}
SENTINELS = {"-999", "-9999", "9999", "999999"}
STEP_HOURS = 6
PERIOD_START = datetime(2026, 1, 1, tzinfo=timezone.utc)
PERIOD_END = datetime(2026, 7, 1, tzinfo=timezone.utc)


def _parse_ts(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def line_rules(row: dict, park: set[str]) -> list[str]:
    rules: list[str] = []
    sensor = str(row.get("sensor_name", "")).strip().lower()
    sensor_raw = str(row.get("sensor_name", ""))
    value_raw = str(row.get("value", ""))

    if sensor not in SENSOR_RANGE:
        rules.append("D-SCHEMA")
    try:
        val = float(value_raw)
    except ValueError:
        rules.append("D-SCHEMA")
        val = None

    moment = _parse_ts(row.get("timestamp", ""))
    if moment is None:
        rules.append("D-FORMAT")
    elif moment.hour % STEP_HOURS or moment.minute or moment.second:
        rules.append("D-FORMAT")
    elif not PERIOD_START <= moment < PERIOD_END:
        rules.append("D-FORMAT")

    if value_raw in SENTINELS or value_raw == "":
        rules.append("D-RANGE")
    elif val is not None and sensor in SENSOR_RANGE:
        lo, hi = SENSOR_RANGE[sensor]
        if not lo <= val <= hi:
            rules.append("D-RANGE")

    if sensor in EXPECTED_UNIT and row.get("unit") != EXPECTED_UNIT[sensor]:
        rules.append("D-UNIT")

    if park and row.get("equipment_id") not in park:
        rules.append("D-FK")

    if value_raw and "." in value_raw and len(value_raw.split(".", 1)[1]) > 3:
        rules.append("D-PRECISION")

    return rules


def multisource_rule(row: dict, events: pd.DataFrame) -> str | None:
    """Détection greffe : mesure calme pendant événement critical sur même équipement."""
    eq = row.get("equipment_id")
    moment = _parse_ts(row.get("timestamp", ""))
    if moment is None or events.empty:
        return None
    ev = events.copy()
    ev["start_at"] = pd.to_datetime(ev["start_at"], utc=True, errors="coerce")
    ev["end_at"] = pd.to_datetime(ev["end_at"], utc=True, errors="coerce")
    crit = ev.loc[
        (ev["equipment_id"] == eq)
        & (ev["severity"].isin(["critical", "high"]))
        & (ev["start_at"] <= moment)
        & (ev["end_at"].fillna(ev["start_at"]) >= moment)
    ]
    if crit.empty:
        return None
    try:
        val = float(row["value"])
    except ValueError:
        return None
    sensor = str(row.get("sensor_name", ""))
    # heuristique : vibration/temp élevées attendues pendant incident ; valeur basse suspecte
    if sensor == "vibration_mm_s" and val < 1.0:
        return "D-MS-EVT"
    if sensor == "temperature_c" and val < 30.0:
        return "D-MS-EVT"
    return None


def classify_line(rules: list[str]) -> str:
    gross = {"D-UNIT", "D-RANGE", "D-SCHEMA", "D-FK", "D-PRECISION", "D-MS-EVT"}
    if any(r in gross for r in rules):
        return "fabriquée"
    if rules == ["D-FORMAT"]:
        return "indécidable"
    if not rules:
        return "réelle"
    return "indécidable"


def detect_control_batch(
    batch_path: Path,
    equipment_path: Path,
    events_path: Path,
) -> pd.DataFrame:
    batch = pd.read_csv(batch_path)
    park = set(pd.read_csv(equipment_path)["equipment_id"].astype(str))
    events = pd.read_csv(events_path)
    rows = []
    for _, row in batch.iterrows():
        rules = line_rules(row.to_dict(), park)
        ms = multisource_rule(row.to_dict(), events)
        if ms:
            rules.append(ms)
        rid = (
            f"{row['equipment_id']}|{row['timestamp']}|{row['sensor_name']}"
        )
        verdict = classify_line(rules)
        rows.append(
            {
                "row_identifier": rid,
                "equipment_id": row["equipment_id"],
                "timestamp": row["timestamp"],
                "sensor_name": row["sensor_name"],
                "verdict": verdict,
                "rule_id": rules[0] if rules else "D-OK",
                "all_rules": ";".join(rules) if rules else "",
            }
        )
    return pd.DataFrame(rows)
