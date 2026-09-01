import pytest

from app.model_client import ModelUpstreamError, normalize_payload
from app.schemas import DiagnoseRequest


def _request() -> DiagnoseRequest:
    return DiagnoseRequest(
        report_id="RPT-2026S1-0001",
        technician_note="Pompe qui vibre fortement depuis deux jours au démarrage",
        equipment_id="EQ-PUMP-001",
    )


def test_normalize_payload_nominal():
    raw = {
        "equipment_id": "IGNORE-ME",
        "symptom": "vibration anormale",
        "severity": "HIGH",
        "failure_hypothesis": "roulement usé",
        "recommended_action": "inspection palier",
        "confidence": 0.82,
        "evidence": [],
        "requires_human_review": False,
    }
    out = normalize_payload(raw, _request())
    assert out.equipment_id == "EQ-PUMP-001"
    assert out.severity == "high"
    assert out.evidence == ["rapport RPT-2026S1-0001"]
    assert out.requires_human_review is False


def test_normalize_force_review_si_confiance_basse():
    raw = {
        "symptom": "bruit",
        "severity": "medium",
        "failure_hypothesis": "indéterminé",
        "recommended_action": "surveiller",
        "confidence": 0.4,
        "evidence": ["x"],
        "requires_human_review": False,
    }
    out = normalize_payload(raw, _request())
    assert out.requires_human_review is True


def test_normalize_force_review_si_note_courte():
    request = DiagnoseRequest(
        report_id="RPT-SHORT",
        technician_note="Machine bizarre",
    )
    raw = {
        "symptom": "indéterminé",
        "severity": "low",
        "failure_hypothesis": "inconnu",
        "recommended_action": "inspecter",
        "confidence": 0.9,
        "evidence": ["x"],
        "requires_human_review": False,
    }
    out = normalize_payload(raw, request)
    assert out.requires_human_review is True
    assert out.confidence <= 0.45


def test_normalize_payload_invalide():
    with pytest.raises(ModelUpstreamError):
        normalize_payload({"symptom": "seul"}, _request())
