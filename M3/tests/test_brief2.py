"""Tests brief 2 — reproductibilité et idempotence logique."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.brief2.augmentation import augment_noise
from src.brief2.detection import classify_line, line_rules
from src.brief2.generation import generate_marginal
from src.brief2.laplace import laplace_mechanism


def test_laplace_is_reproducible_with_seed():
    a = laplace_mechanism(5, 1, 1.0, seed=42)
    b = laplace_mechanism(5, 1, 1.0, seed=42)
    assert a == b


def test_marginal_generation_schema():
    ref = pd.DataFrame(
        [
            {
                "equipment_id": "EQ-A",
                "timestamp": "2026-01-02T00:00:00Z",
                "sensor_name": "temperature_c",
                "value": 50.0,
                "unit": "°C",
                "period": "2026-S1",
            }
        ]
    )
    out = generate_marginal(ref, ["EQ-W1"], seed=1)
    assert set(out.columns) >= {"provenance", "procedure_id", "equipment_id"}
    assert (out["provenance"] == "synthétique").all()


def test_detection_gross_fabrication():
    row = {
        "equipment_id": "EQ-A",
        "timestamp": "2026-01-02T01:23:00Z",
        "sensor_name": "pressure_bar",
        "value": "577",
        "unit": "kPa",
        "period": "2026-S1",
    }
    rules = line_rules(row, {"EQ-A"})
    assert classify_line(rules) == "fabriquée"


def test_augment_noise_adds_provenance():
    s = pd.DataFrame(
        [
            {
                "equipment_id": "EQ-A",
                "timestamp": "2026-01-02T00:00:00Z",
                "timestamp_utc": "2026-01-02T00:00:00Z",
                "sensor_name": "temperature_c",
                "value": 40.0,
                "unit": "°C",
                "period": "2026-S1",
            }
        ]
    )
    out = augment_noise(s, seed=0)
    assert out.iloc[0]["provenance"] == "augmentée"
