"""Partie 2 — techniques d'augmentation de séries existantes."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _series_key(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["_ts"] = pd.to_datetime(out.get("timestamp_utc", out["timestamp"]), utc=True)
    return out.sort_values(["equipment_id", "sensor_name", "_ts"])


def augment_noise(
    series: pd.DataFrame, sigma_frac: float = 0.05, seed: int = 42
) -> pd.DataFrame:
    """Ajout de bruit gaussien proportionnel à l'écart-type de la série."""
    rng = np.random.default_rng(seed)
    work = _series_key(series)
    out_rows = []
    for (_, _), grp in work.groupby(["equipment_id", "sensor_name"], observed=True):
        values = pd.to_numeric(grp["value"], errors="coerce")
        std = float(values.std()) or 1.0
        for _, row in grp.iterrows():
            new = row.copy()
            noise = rng.normal(0, sigma_frac * std)
            new["value"] = round(float(row["value"]) + noise, 2)
            new["provenance"] = "augmentée"
            new["procedure_id"] = "AUG-NOISE-001"
            out_rows.append(new)
    return pd.DataFrame(out_rows)


def augment_time_shift(series: pd.DataFrame, shift_hours: int = 6, seed: int = 42) -> pd.DataFrame:
    """Décalage temporel fixe (+6 h) — préserve amplitude, casse l'alignement événements."""
    work = _series_key(series)
    out_rows = []
    for _, row in work.iterrows():
        new = row.copy()
        ts = row["_ts"] + pd.Timedelta(hours=shift_hours)
        new["timestamp"] = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        if "timestamp_utc" in new:
            new["timestamp_utc"] = new["timestamp"]
        new["provenance"] = "augmentée"
        new["procedure_id"] = "AUG-SHIFT-001"
        out_rows.append(new)
    return pd.DataFrame(out_rows)


AUGMENTATION_META = {
    "AUG-NOISE-001": {
        "preserve": "ordre de grandeur, unité, pas (si appliqué ligne à ligne)",
        "destroy": "valeurs exactes, corrélation fine avec événements",
        "admissible": "tests de robustesse algorithmique",
        "not_admissible": "évaluation de performance nominale",
    },
    "AUG-SHIFT-001": {
        "preserve": "distribution des valeurs, régularité du pas relatif",
        "destroy": "alignement temporel avec events.csv",
        "admissible": "stress-test de fenêtres de rapprochement",
        "not_admissible": "détection cause-effet temporelle",
    },
}
