"""Point de départ des contrats M3.

Les domaines fermés et les identifiants de règles héritées sont fournis pour
éviter la ressaisie. Les schémas, les plages physiques et le rapprochement
temporel restent à définir et à justifier pendant le brief.
"""

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

# Nom de capteur attendu et unité annoncée par ce nom. Le fichier reçu ne
# garantit pas la cohérence entre les deux : c'est un contrôle à écrire.
SENSOR_UNITS = {
    "vibration_mm_s": "mm/s",
    "temperature_c": "°C",
    "pressure_bar": "bar",
    "current_a": "A",
    "rpm": "rpm",
}
EXPECTED_SENSOR_UNITS = SENSOR_UNITS

# Alias observés dans la livraison (casse / orthographe) → nom canonique.
SENSOR_NAME_ALIASES = {
    "TEMPERATURE_C": "temperature_c",
    "Temperature_C": "temperature_c",
    "VIBRATION_MM_S": "vibration_mm_s",
    "PRESSURE_BAR": "pressure_bar",
    "CURRENT_A": "current_a",
    "RPM": "rpm",
}

# Plages physiques plausibles (justifiées dans docs/registre_regles.md).
SENSOR_VALUE_RANGES = {
    "vibration_mm_s": (0.0, 80.0),
    "temperature_c": (-40.0, 200.0),
    "pressure_bar": (-1.0, 100.0),
    "current_a": (0.0, 500.0),
    "rpm": (0.0, 10000.0),
}

MEASUREMENT_KEY = ("equipment_id", "timestamp", "sensor_name")

# Pas d'échantillonnage annoncé dans SCHEMA.md pour la livraison 2026-S1.
# Le pas réellement observé doit être mesuré, pas supposé.
ANNOUNCED_STEP_HOURS = 6
ANNOUNCED_PERIOD = "2026-S1"

# Fenêtre de rapprochement mesures ↔ événements (justifiée dans le diagnostic).
ALIGN_BEFORE_HOURS = 48.0
ALIGN_AFTER_HOURS = 24.0

# Règles de la préparation de référence M2, à reprendre avec un statut explicite.
# Source : data_pack/2026-S1/reference_runs/m2_for_m3/regles_m2.md
M2_RULE_IDS = (
    "R-EQ-001",
    "R-EQ-002",
    "R-EQ-003",
    "R-EQ-004",
    "R-EQ-005",
    "R-EQ-006",
    "R-EVT-001",
    "R-EVT-002",
    "R-EVT-003",
    "R-EVT-004",
    "R-EVT-005",
    "R-MNT-001",
    "R-MNT-002",
    "R-MNT-003",
    "R-MNT-004",
    "R-MNT-005",
    "R-MNT-006",
    "R-MNT-007",
    "R-MNT-008",
)


def sensor_value_ranges():
    """Retourner les plages physiques plausibles par capteur."""
    return dict(SENSOR_VALUE_RANGES)


def sensor_schema():
    """Schéma minimal attendu pour ``sensor_readings.csv``."""
    return {
        "required_columns": [
            "equipment_id",
            "timestamp",
            "sensor_name",
            "value",
            "unit",
            "period",
        ],
        "measurement_key": list(MEASUREMENT_KEY),
        "expected_units": dict(EXPECTED_SENSOR_UNITS),
        "value_ranges": sensor_value_ranges(),
    }


def align_measures_to_events(measures, events, before_hours, after_hours):
    """Rapprocher les mesures des événements par fenêtre temporelle."""
    import pandas as pd

    from src.data_pipeline.timeseries import to_utc, window_bounds

    if measures.empty or events.empty:
        return pd.DataFrame()

    m = measures.copy()
    m["_ts"] = to_utc(m["timestamp_utc"] if "timestamp_utc" in m.columns else m["timestamp"])
    m = m.dropna(subset=["_ts", "equipment_id"])
    m["_mid"] = (
        m["equipment_id"].astype(str)
        + "|"
        + m["timestamp"].astype(str)
        + "|"
        + m["sensor_name"].astype(str)
    )

    bounds = window_bounds(events, before_hours=before_hours, after_hours=after_hours)
    bounds = bounds.dropna(subset=["window_start", "window_end", "equipment_id"])

    pairs: list[dict] = []
    for _, ev in bounds.iterrows():
        eq = str(ev["equipment_id"])
        subset = m.loc[m["equipment_id"].astype(str) == eq]
        if subset.empty:
            continue
        mask = (subset["_ts"] >= ev["window_start"]) & (subset["_ts"] <= ev["window_end"])
        matched = subset.loc[mask]
        for _, row in matched.iterrows():
            pairs.append(
                {
                    "event_id": ev["event_id"],
                    "equipment_id": eq,
                    "measurement_id": row["_mid"],
                    "sensor_name": row["sensor_name"],
                    "timestamp": row["timestamp"],
                    "value": row["value"],
                    "unit": row["unit"],
                    "event_start_at": ev.get("start_at"),
                    "window_start": ev["window_start"].isoformat(),
                    "window_end": ev["window_end"].isoformat(),
                    "before_hours": before_hours,
                    "after_hours": after_hours,
                }
            )
    return pd.DataFrame(pairs)