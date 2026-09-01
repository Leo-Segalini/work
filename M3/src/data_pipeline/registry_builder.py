"""Registre de règles M2 héritées + règles capteurs M3."""

from __future__ import annotations

from contracts.schemas import M2_RULE_IDS
from src.data_pipeline.rules import Rule, RuleRegistry

_M2_META: dict[str, tuple[str, str]] = {
    "R-EQ-001": ("equipment", "`equipment_id` unique"),
    "R-EQ-002": ("equipment", "`criticality` dans le domaine fermé"),
    "R-EQ-003": ("equipment", "`equipment_type` normalisé"),
    "R-EQ-004": ("equipment", "`rated_power_kw` strictement positive"),
    "R-EQ-005": ("equipment", "`commissioning_date` antérieure à la fin de période"),
    "R-EQ-006": ("equipment", "champs descriptifs renseignés"),
    "R-EVT-001": ("events", "`event_id` unique"),
    "R-EVT-002": ("events", "`severity` dans le domaine fermé"),
    "R-EVT-003": ("events", "`event_type` normalisé et dans le domaine"),
    "R-EVT-004": ("events", "`end_at` postérieure à `start_at`"),
    "R-EVT-005": ("events", "`equipment_id` présent dans la table préparée"),
    "R-MNT-001": ("maintenance", "`maintenance_id` unique"),
    "R-MNT-002": ("maintenance", "`event_id` présent dans la table préparée"),
    "R-MNT-003": ("maintenance", "`equipment_id` présent dans la table préparée"),
    "R-MNT-004": ("maintenance", "`closed_at` postérieure à `opened_at`"),
    "R-MNT-005": ("maintenance", "`downtime_minutes` positive et plausible"),
    "R-MNT-006": ("maintenance", "`parts_cost_eur` positive"),
    "R-MNT-007": ("maintenance", "`intervention_type` normalisé et dans le domaine"),
    "R-MNT-008": ("maintenance", "absence d'information personnelle directe dans les notes"),
}

_SENSOR_RULES = [
    Rule(
        "SEN-NAME-001",
        "sensors",
        "nouvelle",
        "alias de `sensor_name` normalisé",
        justification="casse/orthographe observée (ex. TEMPERATURE_C)",
    ),
    Rule(
        "SEN-NAME-002",
        "sensors",
        "nouvelle",
        "nom de capteur hors contrat → exclusion",
    ),
    Rule(
        "SEN-VAL-001",
        "sensors",
        "nouvelle",
        "valeur non numérique → exclusion",
    ),
    Rule(
        "SEN-TS-001",
        "sensors",
        "nouvelle",
        "horodatage illisible → exclusion ; fuseau manquant interprété UTC",
        justification="hypothèse UTC documentée ; pas de fuseau inventé silencieux",
    ),
    Rule(
        "SEN-UNIT-001",
        "sensors",
        "nouvelle",
        "conversion d'unité déterministe (kPa→bar, K→°C)",
        justification="valeurs ~500–600 en kPa cohérentes avec quelques bars",
    ),
    Rule(
        "SEN-UNIT-002",
        "sensors",
        "nouvelle",
        "unité incompatible sans conversion sûre → exclusion",
    ),
    Rule(
        "SEN-SENT-001",
        "sensors",
        "nouvelle",
        "valeur sentinelle (-999, …) → exclusion",
    ),
    Rule(
        "SEN-RANGE-001",
        "sensors",
        "nouvelle",
        "hors plage physique plausible → exclusion",
        justification="bornes dans SENSOR_VALUE_RANGES, issues de l'audit",
    ),
    Rule(
        "SEN-FK-001",
        "sensors",
        "nouvelle",
        "`equipment_id` absent de equipment préparé → exclusion",
    ),
    Rule(
        "SEN-DUP-001",
        "sensors",
        "nouvelle",
        "doublon strict de clé logique → une ligne conservée",
    ),
    Rule(
        "SEN-DUP-002",
        "sensors",
        "nouvelle",
        "doublon conflictuel (valeurs divergentes) → exclusion",
    ),
    Rule(
        "SEN-ALIGN-001",
        "sensors",
        "nouvelle",
        "rapprochement événement ±48h / +24h",
        justification="couvre un pré-signal et un suivi court sans causalité affirmée",
    ),
]


def build_registry() -> RuleRegistry:
    registry = RuleRegistry()
    for rule_id in M2_RULE_IDS:
        table, description = _M2_META[rule_id]
        registry.add(
            Rule(
                rule_id=rule_id,
                table=table,
                status="conservee",
                description=description,
                origin="M2",
                justification="réutilisée via référence m2_for_m3 sans modification de comportement",
            )
        )
    registry.extend(_SENSOR_RULES)
    return registry
