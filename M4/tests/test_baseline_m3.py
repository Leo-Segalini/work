"""Tests baseline M3."""

from src.baseline_m3 import predict_row, rule_hits


def test_fabricated_unit_triggers_m3_unit():
    row = {
        "equipment_id": "EQ-A",
        "timestamp": "2026-01-02T00:00:00Z",
        "sensor_name": "pressure_bar",
        "value": "5.0",
        "unit": "kPa",
        "period": "2026-S1",
    }
    assert "M3-UNIT" in rule_hits(row)
    assert predict_row(row)[0] == "fabriquée"


def test_valid_row_is_real():
    row = {
        "equipment_id": "EQ-A",
        "timestamp": "2026-01-02T00:00:00Z",
        "sensor_name": "pressure_bar",
        "value": "5.0",
        "unit": "bar",
        "period": "2026-S1",
    }
    assert predict_row(row)[0] == "réelle"
