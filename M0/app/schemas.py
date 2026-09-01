"""Schémas Pydantic du contrat DiagOps M0."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


Severity = Literal["low", "medium", "high", "critical"]


class DiagnoseRequest(BaseModel):
    """Entrée de la route POST /diagnose."""

    report_id: str = Field(..., min_length=1)
    technician_note: str = Field(..., min_length=1)
    equipment_id: str | None = None

    @field_validator("report_id", "technician_note")
    @classmethod
    def strip_non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("le champ ne peut pas être vide")
        return cleaned

    @field_validator("equipment_id")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class DiagnoseResponse(BaseModel):
    """Sortie structurée conforme au contrat DiagOps."""

    equipment_id: str | None = None
    symptom: str = Field(..., min_length=1)
    severity: Severity
    failure_hypothesis: str = Field(..., min_length=1)
    recommended_action: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: list[str] = Field(..., min_length=1)
    requires_human_review: bool
