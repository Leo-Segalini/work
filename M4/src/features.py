"""Features capteurs agrégées par fenêtre et par ligne."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean, pstdev

from .baseline_m3 import rule_feature_vector, rule_hits


def group_windows(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["window_id"]].append(row)
    return dict(grouped)


def numeric_summary(rows: list[dict[str, str]]) -> dict[str, float]:
    values: list[float] = []
    missing = 0
    for row in rows:
        try:
            values.append(float(row["value"]))
        except ValueError:
            missing += 1
    return {
        "value_mean": mean(values) if values else 0.0,
        "value_std": pstdev(values) if len(values) > 1 else 0.0,
        "missing_share": missing / len(rows) if rows else 0.0,
    }


def build_feature_table(rows: list[dict[str, str]]) -> list[dict[str, float | str]]:
    """Agrégat par fenêtre — point de départ descriptif."""
    return [
        {"window_id": window_id, **numeric_summary(window_rows)}
        for window_id, window_rows in sorted(group_windows(rows).items())
    ]


SENSOR_INDEX = {
    "vibration_mm_s": 0,
    "temperature_c": 1,
    "pressure_bar": 2,
    "current_a": 3,
    "rpm": 4,
}


def row_features(row: dict[str, str]) -> dict[str, float]:
    """Vecteur de features ligne pour modèles simples."""
    feats = rule_feature_vector(row)
    try:
        feats["value"] = float(row["value"])
    except ValueError:
        feats["value"] = 0.0
        feats["M3-MISSING"] = 1.0
    sensor = row.get("sensor_name", "")
    for name, idx in SENSOR_INDEX.items():
        feats[f"sensor_{idx}"] = 1.0 if sensor == name else 0.0
    return feats


def feature_matrix(rows: list[dict[str, str]]) -> tuple[list[str], list[list[float]]]:
    """Retourne noms de colonnes et matrice X."""
    if not rows:
        return [], []
    names = sorted(row_features(rows[0]).keys())
    matrix = [[row_features(row)[name] for name in names] for row in rows]
    return names, matrix


def labels(rows: list[dict[str, str]], positive: str = "fabriquée") -> list[int]:
    return [1 if row.get("provenance") == positive else 0 for row in rows]
