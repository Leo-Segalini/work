"""Client Hugging Face Inference pour le diagnostic DiagOps."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from huggingface_hub import InferenceClient

from app.schemas import DiagnoseRequest, DiagnoseResponse, Severity

logger = logging.getLogger(__name__)

HF_TIMEOUT_SECONDS = 60
CONFIDENCE_REVIEW_THRESHOLD = 0.6
DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"

SEVERITY_MAP = {
    "low": "low",
    "faible": "low",
    "medium": "medium",
    "moyen": "medium",
    "moyenne": "medium",
    "high": "high",
    "élevé": "high",
    "eleve": "high",
    "élevée": "high",
    "elevee": "high",
    "critical": "critical",
    "critique": "critical",
}

SYSTEM_PROMPT = """Tu es un assistant de diagnostic de maintenance industrielle DiagOps.
Réponds UNIQUEMENT avec un objet JSON valide (pas de markdown) ayant exactement ces clés :
equipment_id (string|null), symptom (string), severity (low|medium|high|critical),
failure_hypothesis (string), recommended_action (string), confidence (nombre 0..1),
evidence (liste de strings), requires_human_review (boolean).
Base-toi uniquement sur le rapport technicien. N'invente pas de faits absents du texte.
Si l'information est insuffisante, baisse confidence et mets requires_human_review à true.
Réponds en français pour les champs textuels."""


class ModelClientError(Exception):
    """Erreur métier liée au modèle."""


class ModelConfigError(ModelClientError):
    """Configuration manquante (token, etc.)."""


class ModelUpstreamError(ModelClientError):
    """Échec appel HF ou sortie non exploitable."""


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ModelUpstreamError("réponse modèle sans JSON exploitable") from None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise ModelUpstreamError("JSON modèle invalide") from exc


def _normalize_severity(value: Any) -> Severity:
    key = str(value).strip().lower()
    mapped = SEVERITY_MAP.get(key)
    if mapped is None:
        raise ModelUpstreamError(f"severity invalide: {value!r}")
    return mapped  # type: ignore[return-value]


def normalize_payload(raw: dict[str, Any], request: DiagnoseRequest) -> DiagnoseResponse:
    """Normalise un dict brut en DiagnoseResponse ou lève ModelUpstreamError."""
    try:
        symptom = str(raw.get("symptom", "")).strip()
        hypothesis = str(raw.get("failure_hypothesis", "")).strip()
        action = str(raw.get("recommended_action", "")).strip()
        confidence = float(raw.get("confidence", 0.0))
        confidence = max(0.0, min(1.0, confidence))
        severity = _normalize_severity(raw.get("severity", "medium"))
        evidence_raw = raw.get("evidence") or []
        if not isinstance(evidence_raw, list):
            evidence_raw = [str(evidence_raw)]
        evidence = [str(item).strip() for item in evidence_raw if str(item).strip()]
        if not evidence:
            evidence = [f"rapport {request.report_id}"]
        review = bool(raw.get("requires_human_review", False))
        # Confiance basse ou note trop courte / vague → revue humaine obligatoire.
        if confidence < CONFIDENCE_REVIEW_THRESHOLD:
            review = True
        if len(request.technician_note) < 40:
            review = True
            confidence = min(confidence, 0.45)
        equipment_id = request.equipment_id
        if equipment_id is None:
            eid = raw.get("equipment_id")
            equipment_id = str(eid).strip() if eid else None
        return DiagnoseResponse(
            equipment_id=equipment_id,
            symptom=symptom,
            severity=severity,
            failure_hypothesis=hypothesis,
            recommended_action=action,
            confidence=confidence,
            evidence=evidence,
            requires_human_review=review,
        )
    except ModelUpstreamError:
        raise
    except (TypeError, ValueError) as exc:
        raise ModelUpstreamError("payload modèle non conforme") from exc


def diagnose_hf_api(request: DiagnoseRequest) -> DiagnoseResponse:
    """Appelle Hugging Face Inference et retourne un diagnostic normalisé."""
    token = os.getenv("HF_TOKEN", "").strip()
    if not token:
        raise ModelConfigError("HF_TOKEN manquant : définir la clé dans .env")
    model = os.getenv("HF_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    client = InferenceClient(token=token, timeout=HF_TIMEOUT_SECONDS)
    user_content = (
        f"report_id: {request.report_id}\n"
        f"equipment_id: {request.equipment_id or 'null'}\n"
        f"technician_note: {request.technician_note}"
    )
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            max_tokens=512,
            temperature=0.2,
        )
        content = completion.choices[0].message.content or ""
    except ModelClientError:
        raise
    except Exception as exc:  # noqa: BLE001 — encapsuler toute erreur HF
        logger.exception("échec appel Hugging Face")
        raise ModelUpstreamError(f"échec appel Hugging Face: {exc}") from exc
    raw = _extract_json(content)
    return normalize_payload(raw, request)


def diagnose(request: DiagnoseRequest) -> DiagnoseResponse:
    """Route vers le provider configuré (hf_api | local_baseline | local_lora)."""
    provider = os.getenv("MODEL_PROVIDER", "hf_api").strip().lower() or "hf_api"
    if provider == "hf_api":
        return diagnose_hf_api(request)
    if provider == "local_baseline":
        from app.local_provider import diagnose_local

        return diagnose_local(request, with_adapter=False)
    if provider == "local_lora":
        from app.local_provider import diagnose_local

        return diagnose_local(request, with_adapter=True)
    raise ModelConfigError(
        f"MODEL_PROVIDER inconnu: {provider!r} "
        "(attendu: hf_api | local_baseline | local_lora)"
    )
