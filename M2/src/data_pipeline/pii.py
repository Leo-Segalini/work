"""Détection et masquage des données personnelles dans les notes M2."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.\w+", re.IGNORECASE)
# Formats FR courants : 06 12 34 56 78, 06.12.34.56.78, +33 6...
PHONE_RE = re.compile(
    r"(?:\+33|0)\s*[1-9](?:[\s.-]*\d{2}){4}",
    re.IGNORECASE,
)
# Heuristique légère : "Prénom X." ou "Mme/M. Nom"
PERSON_RE = re.compile(
    r"\b(?:Mme|M\.|Mr|Mrs)\s+[A-ZÉÈÊÀÂÙÛÔÎÇ][\w'-]+"
    r"|\b[A-ZÉÈÊÀÂÙÛÔÎÇ][a-zéèêàâùûôîç'-]+\s+[A-Z]\.(?=\s|$|,|;)",
)


def _record(
    source_file: str,
    row_id: Any,
    rule_id: str,
    column: str,
    observed: Any,
    reason: str,
    decision: str,
) -> dict[str, Any]:
    return {
        "source_file": source_file,
        "row_identifier": str(row_id),
        "rule_id": rule_id,
        "column": column,
        "observed_value": "" if observed is None else str(observed),
        "reason": reason,
        "decision": decision,
    }


def mask_pii(text: str) -> tuple[str, list[str]]:
    """Masque email/téléphone/indices de personne. Retourne texte + types trouvés."""
    found: list[str] = []
    masked = text
    if EMAIL_RE.search(masked):
        found.append("email")
        masked = EMAIL_RE.sub("[EMAIL_MASQUE]", masked)
    if PHONE_RE.search(masked):
        found.append("telephone")
        masked = PHONE_RE.sub("[TEL_MASQUE]", masked)
    if PERSON_RE.search(masked):
        found.append("personne")
        masked = PERSON_RE.sub("[PERSONNE_MASQUEE]", masked)
    return masked, found


def scan_notes_for_pii(
    frame: pd.DataFrame,
    *,
    source_file: str,
    id_col: str,
    note_col: str = "work_order_note",
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Scan PII : masque dans une copie et produit des lignes de quarantaine."""
    if note_col not in frame.columns:
        return frame.copy(), []

    out = frame.copy()
    records: list[dict[str, Any]] = []
    masked_values: list[str] = []

    for _, row in out.iterrows():
        raw = "" if pd.isna(row[note_col]) else str(row[note_col])
        masked, kinds = mask_pii(raw)
        masked_values.append(masked)
        for kind in kinds:
            rule = {
                "email": "PII-EMAIL",
                "telephone": "PII-PHONE",
                "personne": "PII-PERSON",
            }[kind]
            records.append(
                _record(
                    source_file,
                    row[id_col],
                    rule,
                    note_col,
                    raw,
                    f"information personnelle détectée ({kind})",
                    "mask_and_keep",
                )
            )

    out[note_col] = masked_values
    return out, records
