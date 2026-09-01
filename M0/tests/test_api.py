from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.model_client import ModelConfigError, ModelUpstreamError
from app.schemas import DiagnoseResponse

client = TestClient(app)


def test_diagnose_nominal():
    fake = DiagnoseResponse(
        equipment_id="EQ-PUMP-001",
        symptom="vibration",
        severity="high",
        failure_hypothesis="roulement",
        recommended_action="inspection",
        confidence=0.8,
        evidence=["rapport RPT-1"],
        requires_human_review=False,
    )
    with patch("app.main.diagnose", return_value=fake) as mocked:
        response = client.post(
            "/diagnose",
            json={
                "report_id": "RPT-1",
                "technician_note": "Pompe qui vibre fort",
                "equipment_id": "EQ-PUMP-001",
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["symptom"] == "vibration"
    assert body["severity"] == "high"
    mocked.assert_called_once()


def test_diagnose_note_vide_422():
    response = client.post(
        "/diagnose",
        json={"report_id": "RPT-1", "technician_note": "  "},
    )
    assert response.status_code == 422


def test_diagnose_config_manquante_503():
    with patch(
        "app.main.diagnose",
        side_effect=ModelConfigError("HF_TOKEN manquant"),
    ):
        response = client.post(
            "/diagnose",
            json={
                "report_id": "RPT-1",
                "technician_note": "Pompe qui vibre fort au démarrage depuis hier",
            },
        )
    assert response.status_code == 503
    assert "HF_TOKEN" in response.json()["detail"]


def test_diagnose_upstream_502():
    with patch(
        "app.main.diagnose",
        side_effect=ModelUpstreamError("JSON modèle invalide"),
    ):
        response = client.post(
            "/diagnose",
            json={
                "report_id": "RPT-1",
                "technician_note": "Pompe qui vibre fort au démarrage depuis hier",
            },
        )
    assert response.status_code == 502


def test_diagnose_provider_inconnu_503():
    with patch.dict("os.environ", {"MODEL_PROVIDER": "inconnu"}, clear=False):
        # Appeler la vraie fonction diagnose (pas main patchée)
        from app.model_client import ModelConfigError, diagnose
        from app.schemas import DiagnoseRequest

        try:
            diagnose(
                DiagnoseRequest(
                    report_id="RPT-1",
                    technician_note="Pompe qui vibre fort au démarrage depuis hier",
                )
            )
            raised = False
        except ModelConfigError:
            raised = True
        assert raised is True
