"""Tests brief 2."""

from pathlib import Path

from src.brief2.audit import audit_transmissibility
from src.brief2.extended_threats import run_extended_threats
from src.brief2.qualification import qualify_sensor_test


def test_audit_finds_core_artifacts():
    root = Path(__file__).resolve().parents[1]
    report = audit_transmissibility(root)
    assert report["artifacts_checked"] >= 8
    assert "configs/model.yaml" not in report["missing"]


def test_sensor_test_has_no_labels():
    root = Path(__file__).resolve().parents[1]
    data = root / "../../data_pack/2026-S1/model_eval/sensor_test.csv"
    q = qualify_sensor_test(data.resolve())
    assert q["rows"] == 1800
    assert q["has_provenance_label"] is False


def test_extended_threats_pass():
    checks = run_extended_threats()
    assert all(c["passed"] for c in checks)
