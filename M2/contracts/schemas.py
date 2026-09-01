"""Schémas / domaines fermés M2 (point de départ justifié)."""

SEVERITIES = {"low", "medium", "high", "critical"}
CRITICALITIES = {"low", "medium", "high", "critical"}
EVENT_TYPES = {"incident", "intervention", "observation", "alert"}
INTERVENTION_TYPES = {
    "inspection",
    "corrective",
    "preventive",
    "calibration",
    "replacement",
}
OUTCOMES = {
    "resolved",
    "monitoring",
    "parts_ordered",
    "no_fault_found",
    "follow_up_required",
}

# Contrats appliqués via validation.py (contrôles Pandas explicites).
# Pandera reste optionnel ; les domaines ci-dessus sont la référence métier.
