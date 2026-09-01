"""Tests de préparation capteurs — exclusion des données suspectes."""

from __future__ import annotations

import pandas as pd

from src.data_pipeline.sensors import prepare_sensors


def _frame(rows):
    return pd.DataFrame(
        rows,
        columns=["equipment_id", "timestamp", "sensor_name", "value", "unit", "period"],
    )


def test_sentinel_and_orphan_are_excluded():
    sensors = _frame(
        [
            ("EQ-A", "2026-01-02T00:00:00Z", "temperature_c", -999.0, "°C", "2026-S1"),
            ("EQ-ORPHAN", "2026-01-02T00:00:00Z", "temperature_c", 40.0, "°C", "2026-S1"),
            ("EQ-A", "2026-01-02T06:00:00Z", "temperature_c", 41.0, "°C", "2026-S1"),
        ]
    )
    processed, quarantine, stats = prepare_sensors(sensors, {"EQ-A"})
    assert stats["kept"] == 1
    assert set(quarantine["rule_id"]) >= {"SEN-SENT-001", "SEN-FK-001"}
    assert processed.iloc[0]["value"] == 41.0


def test_kpa_is_converted_not_silently_dropped():
    sensors = _frame(
        [
            ("EQ-A", "2026-01-02T00:00:00Z", "pressure_bar", 577.0, "kPa", "2026-S1"),
        ]
    )
    processed, quarantine, stats = prepare_sensors(sensors, {"EQ-A"})
    assert stats["kept"] == 1
    assert abs(float(processed.iloc[0]["value"]) - 5.77) < 1e-9
    assert processed.iloc[0]["unit"] == "bar"
    assert "SEN-UNIT-001" in set(quarantine["rule_id"])
    assert "valeur_normalisee" in set(quarantine["decision"])


def test_temperature_alias_is_normalized():
    sensors = _frame(
        [
            ("EQ-A", "2026-01-02T00:00:00Z", "TEMPERATURE_C", 55.0, "°C", "2026-S1"),
        ]
    )
    processed, quarantine, _ = prepare_sensors(sensors, {"EQ-A"})
    assert processed.iloc[0]["sensor_name"] == "temperature_c"
    assert "SEN-NAME-001" in set(quarantine["rule_id"])


def test_conflicting_duplicate_key_is_excluded():
    sensors = _frame(
        [
            ("EQ-A", "2026-01-02T00:00:00Z", "temperature_c", 55.0, "°C", "2026-S1"),
            ("EQ-A", "2026-01-02T00:00:00Z", "temperature_c", 66.0, "°C", "2026-S1"),
        ]
    )
    processed, quarantine, stats = prepare_sensors(sensors, {"EQ-A"})
    assert stats["kept"] == 0
    assert "SEN-DUP-002" in set(quarantine["rule_id"])
