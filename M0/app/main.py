"""API FastAPI DiagOps — Module 0."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.model_client import ModelConfigError, ModelUpstreamError, diagnose
from app.schemas import DiagnoseRequest, DiagnoseResponse

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("diagops.api")

app = FastAPI(
    title="DiagOps M0",
    description=(
        "Assistance au diagnostic de maintenance industrielle. "
        "Entrée : rapport technicien. Sortie : JSON DiagOps validé."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", summary="Santé de l'API")
def health() -> dict[str, str]:
    """Indique si le service HTTP est disponible (ne vérifie pas HF)."""
    return {"status": "ok"}


@app.post(
    "/diagnose",
    response_model=DiagnoseResponse,
    summary="Diagnostiquer un rapport technicien",
    responses={
        200: {"description": "Diagnostic structuré conforme au contrat DiagOps"},
        422: {"description": "Entrée invalide (champs manquants ou note vide)"},
        502: {"description": "Échec du modèle ou JSON non conforme"},
        503: {"description": "Configuration manquante (ex. HF_TOKEN)"},
    },
)
def post_diagnose(payload: DiagnoseRequest) -> DiagnoseResponse:
    """Diagnostique un rapport technicien via un modèle HF sur étagère.

    - Valide l'entrée (Pydantic).
    - Appelle le modèle Instruction Hugging Face Inference.
    - Normalise et valide la sortie avant réponse.
    - Force `requires_human_review` si confiance basse ou note trop courte.
    """
    started = time.perf_counter()
    try:
        result = diagnose(payload)
    except ModelConfigError as exc:
        logger.error("config modèle: report_id=%s err=%s", payload.report_id, exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ModelUpstreamError as exc:
        logger.error("upstream modèle: report_id=%s err=%s", payload.report_id, exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "diagnose ok report_id=%s duration_ms=%.1f review=%s",
        payload.report_id,
        elapsed_ms,
        result.requires_human_review,
    )
    return result
