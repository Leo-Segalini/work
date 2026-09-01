"""Partie 3 — génération pour périmètre non instrumenté (SITE-OUEST)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors

SENSOR_UNITS = {
    "temperature_c": "°C",
    "pressure_bar": "bar",
    "current_a": "A",
}
STEP_HOURS = 6


def _timestamps(start: str, end: str) -> list[str]:
    idx = pd.date_range(start=start, end=end, freq=f"{STEP_HOURS}h", tz="UTC")
    return [t.strftime("%Y-%m-%dT%H:%M:%SZ") for t in idx]


def generate_marginal(
    reference: pd.DataFrame,
    equipment_ids: list[str],
    sensor_name: str = "temperature_c",
    period: str = "2026-S1",
    seed: int = 42,
) -> pd.DataFrame:
    """Tirage indépendant par colonne (équipement, timestamp, valeur)."""
    rng = np.random.default_rng(seed)
    ref = reference.loc[reference["sensor_name"] == sensor_name].copy()
    values = pd.to_numeric(ref["value"], errors="coerce").dropna()
    stamps = _timestamps("2026-02-01T00:00:00Z", "2026-02-07T18:00:00Z")
    rows = []
    for eq in equipment_ids:
        for ts in stamps:
            rows.append(
                {
                    "equipment_id": eq,
                    "timestamp": ts,
                    "timestamp_utc": ts,
                    "sensor_name": sensor_name,
                    "value": round(float(rng.choice(values)), 2),
                    "unit": SENSOR_UNITS[sensor_name],
                    "period": period,
                    "provenance": "synthétique",
                    "procedure_id": "GEN-MARG-001",
                }
            )
    return pd.DataFrame(rows)


def _encode_row(row: pd.Series, sensors: list[str]) -> np.ndarray:
    """Encodage minimal pour SMOTE : capteur one-hot + valeur."""
    vec = [float(row["value"])]
    for s in sensors:
        vec.append(1.0 if row["sensor_name"] == s else 0.0)
    return np.array(vec, dtype=float)


def generate_smote(
    reference: pd.DataFrame,
    equipment_ids: list[str],
    n_rows: int = 120,
    seed: int = 42,
) -> pd.DataFrame:
    """Interpolation entre voisins (SMOTE manuel) — traitement catégoriel explicite."""
    rng = np.random.default_rng(seed)
    ref = reference.copy()
    ref["value"] = pd.to_numeric(ref["value"], errors="coerce")
    ref = ref.dropna(subset=["value"])
    sensors = sorted(ref["sensor_name"].unique())
    X = np.vstack([_encode_row(r, sensors) for _, r in ref.iterrows()])
    nn = NearestNeighbors(n_neighbors=6, metric="euclidean").fit(X)
    stamps = _timestamps("2026-02-08T00:00:00Z", "2026-02-14T18:00:00Z")
    rows = []
    for i in range(n_rows):
        idx = int(rng.integers(0, len(ref)))
        dist, ind = nn.kneighbors(X[idx : idx + 1], n_neighbors=6)
        neighbor_idx = int(ind[0][1])  # exclure soi-même
        alpha = float(rng.random())
        blended = X[idx] * (1 - alpha) + X[neighbor_idx] * alpha
        value = round(float(blended[0]), 2)
        sensor_idx = int(np.argmax(blended[1:]))
        sensor = sensors[sensor_idx]
        eq = equipment_ids[i % len(equipment_ids)]
        ts = stamps[i % len(stamps)]
        rows.append(
            {
                "equipment_id": eq,
                "timestamp": ts,
                "timestamp_utc": ts,
                "sensor_name": sensor,
                "value": value,
                "unit": SENSOR_UNITS.get(sensor, ref.loc[ref.sensor_name == sensor, "unit"].iloc[0]),
                "period": "2026-S1",
                "provenance": "synthétique",
                "procedure_id": "GEN-SMOTE-001",
            }
        )
    return pd.DataFrame(rows)


def pick_site_ouest_equipment(processed_dir: Path, max_n: int = 3) -> list[str]:
    eq = pd.read_csv(processed_dir / "equipment.csv")
    sensors = pd.read_csv(processed_dir / "sensor_readings.csv")
    inst = set(sensors["equipment_id"])
    candidates = eq.loc[
        (eq["site_id"] == "SITE-OUEST") & (~eq["equipment_id"].isin(inst)), "equipment_id"
    ].astype(str)
    return candidates.head(max_n).tolist()


def compare_real_vs_synthetic(real: pd.DataFrame, synthetic: pd.DataFrame) -> dict:
    """Compare marginales et corrélation value~sensor (proxy relation inter-colonnes)."""
    real_v = pd.to_numeric(real["value"], errors="coerce")
    syn_v = pd.to_numeric(synthetic["value"], errors="coerce")
    out = {
        "marginals": {
            "real_mean": round(float(real_v.mean()), 3),
            "syn_mean": round(float(syn_v.mean()), 3),
            "real_std": round(float(real_v.std()), 3),
            "syn_std": round(float(syn_v.std()), 3),
        },
        "correlation_sensor_value_real": round(
            float(real.assign(v=real_v).groupby("sensor_name")["v"].mean().std() or 0), 3
        ),
        "correlation_sensor_value_syn": round(
            float(synthetic.assign(v=syn_v).groupby("sensor_name")["v"].mean().std() or 0), 3
        ),
        "note": "Le tirage marginal détruit les corrélations inter-capteurs ; SMOTE les partiellement.",
    }
    return out
