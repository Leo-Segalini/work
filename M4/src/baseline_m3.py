"""Baseline M3 figée — règles de provenance capteurs (référence formateur)."""

from __future__ import annotations

from datetime import datetime

EXPECTED_UNIT = {
    "vibration_mm_s": "mm/s",
    "temperature_c": "°C",
    "pressure_bar": "bar",
    "current_a": "A",
    "rpm": "rpm",
}
RANGES = {
    "vibration_mm_s": (0.0, 12.0),
    "temperature_c": (-20.0, 140.0),
    "pressure_bar": (0.0, 25.0),
    "current_a": (0.0, 120.0),
    "rpm": (0.0, 3000.0),
}
RULE_NAMES = [
    "M3-PERIOD",
    "M3-SENSOR",
    "M3-UNIT",
    "M3-TIMESTAMP",
    "M3-GRID",
    "M3-MISSING",
    "M3-SENTINEL",
    "M3-RANGE",
    "M3-PRECISION",
]


def parse_timestamp(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def rule_hits(row: dict[str, str]) -> list[str]:
    hits: list[str] = []
    sensor = row.get("sensor_name", "")
    value = row.get("value", "")
    timestamp = row.get("timestamp", "")

    if row.get("period") != "2026-S1":
        hits.append("M3-PERIOD")
    if sensor not in EXPECTED_UNIT:
        hits.append("M3-SENSOR")
    elif row.get("unit") != EXPECTED_UNIT[sensor]:
        hits.append("M3-UNIT")

    moment = parse_timestamp(timestamp)
    if moment is None or not timestamp.endswith("Z"):
        hits.append("M3-TIMESTAMP")
    elif moment.minute != 0 or moment.second != 0 or moment.hour % 6:
        hits.append("M3-GRID")

    try:
        numeric = float(value)
    except ValueError:
        hits.append("M3-MISSING")
    else:
        if numeric == -999.0:
            hits.append("M3-SENTINEL")
        if sensor in RANGES:
            low, high = RANGES[sensor]
            if numeric < low or numeric > high:
                hits.append("M3-RANGE")
        decimals = value.partition(".")[2]
        if len(decimals) > 2:
            hits.append("M3-PRECISION")
    return hits


def predict_row(row: dict[str, str]) -> tuple[str, str]:
    hits = rule_hits(row)
    return ("fabriquée" if hits else "réelle", ";".join(hits) or "none")


def rule_feature_vector(row: dict[str, str]) -> dict[str, float]:
    hits = set(rule_hits(row))
    return {name: 1.0 if name in hits else 0.0 for name in RULE_NAMES}
