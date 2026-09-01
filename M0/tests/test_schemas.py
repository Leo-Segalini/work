import pytest
from pydantic import ValidationError

from app.schemas import DiagnoseRequest, DiagnoseResponse


def test_diagnose_request_rejette_note_vide():
    with pytest.raises(ValidationError):
        DiagnoseRequest(report_id="RPT-1", technician_note="   ")


def test_diagnose_response_valide():
    resp = DiagnoseResponse(
        equipment_id="EQ-1",
        symptom="vibration",
        severity="high",
        failure_hypothesis="roulement",
        recommended_action="inspection",
        confidence=0.7,
        evidence=["rapport RPT-1"],
        requires_human_review=True,
    )
    assert resp.severity == "high"
    assert 0.0 <= resp.confidence <= 1.0
