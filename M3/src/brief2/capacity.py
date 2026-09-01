"""Partie 1 — mesurer ce que le jeu de données ne permet pas."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from contracts.schemas import ALIGN_AFTER_HOURS, ALIGN_BEFORE_HOURS


def _data_root(explicit: Path | None) -> Path:
    if explicit:
        return explicit.resolve()
    roots = [Path.cwd().resolve(), *Path.cwd().resolve().parents]
    for root in roots:
        candidate = root / "data_pack" / "2026-S1"
        if (candidate / "sensors" / "sensor_readings.csv").is_file():
            return candidate
    raise FileNotFoundError("data_pack/2026-S1 introuvable")


def load_context(data_dir: Path | None, processed_dir: Path) -> dict[str, pd.DataFrame]:
    root = _data_root(data_dir)
    return {
        "equipment": pd.read_csv(processed_dir / "equipment.csv"),
        "events": pd.read_csv(processed_dir / "events.csv"),
        "maintenance": pd.read_csv(processed_dir / "maintenance_history.csv"),
        "sensors_raw": pd.read_csv(root / "sensors" / "sensor_readings.csv"),
        "sensors_processed": pd.read_csv(processed_dir / "sensor_readings.csv"),
    }


def alignment_rate(events: pd.DataFrame, sensors: pd.DataFrame) -> pd.DataFrame:
    """Part des événements avec au moins une mesure dans la fenêtre."""
    ev = events.copy()
    sen = sensors.copy()
    ev["start_at"] = pd.to_datetime(ev["start_at"], utc=True, errors="coerce")
    ev["end_at"] = pd.to_datetime(ev["end_at"], utc=True, errors="coerce")
    sen["timestamp_utc"] = pd.to_datetime(
        sen.get("timestamp_utc", sen["timestamp"]), utc=True, errors="coerce"
    )
    rates = []
    for severity, grp in ev.groupby("severity", dropna=False):
        matched = 0
        for _, row in grp.iterrows():
            start = row["start_at"]
            end = row["end_at"] if pd.notna(row["end_at"]) else start
            w0 = start - pd.Timedelta(hours=ALIGN_BEFORE_HOURS)
            w1 = end + pd.Timedelta(hours=ALIGN_AFTER_HOURS)
            sub = sen[
                (sen["equipment_id"] == row["equipment_id"])
                & (sen["timestamp_utc"] >= w0)
                & (sen["timestamp_utc"] <= w1)
            ]
            if len(sub):
                matched += 1
        rates.append(
            {
                "severity": severity,
                "events": len(grp),
                "with_measures": matched,
                "rate": round(matched / len(grp), 4) if len(grp) else 0.0,
            }
        )
    return pd.DataFrame(rates)


def segment_park(equipment: pd.DataFrame, n_clusters: int = 4) -> pd.DataFrame:
    """Segmentation KMeans sur variables numériques + encodage site/type."""
    work = equipment.copy()
    work["commissioning_date"] = pd.to_datetime(work["commissioning_date"], errors="coerce")
    work["age_years"] = (pd.Timestamp("2026-07-01") - work["commissioning_date"]).dt.days / 365.25
    work["rated_power_kw"] = pd.to_numeric(work["rated_power_kw"], errors="coerce").fillna(
        work["rated_power_kw"].median()
    )
    crit_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    work["criticality_ord"] = work["criticality"].map(crit_map).fillna(2)
    site_d = pd.get_dummies(work["site_id"], prefix="site")
    type_d = pd.get_dummies(work["equipment_type"], prefix="type")
    features = pd.concat(
        [work[["age_years", "rated_power_kw", "criticality_ord"]], site_d, type_d], axis=1
    )
    scaled = StandardScaler().fit_transform(features)
    labels = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit_predict(scaled)
    work["segment_id"] = labels
    return work


def analyse_capacity(data_dir: Path | None, processed_dir: Path) -> dict:
    ctx = load_context(data_dir, processed_dir)
    eq, ev, sensors = ctx["equipment"], ctx["events"], ctx["sensors_processed"]
    inst = set(sensors["equipment_id"].astype(str))
    eq = eq.copy()
    eq["instrumented"] = eq["equipment_id"].astype(str).isin(inst)

    by_site = eq.groupby("site_id").agg(n=("equipment_id", "count"), inst=("instrumented", "sum"))
    by_site["coverage"] = (by_site["inst"] / by_site["n"]).round(4)

    by_crit = eq.groupby("criticality").agg(n=("equipment_id", "count"), inst=("instrumented", "sum"))
    by_crit["coverage"] = (by_crit["inst"] / by_crit["n"]).round(4)

    sev_counts = ev["severity"].value_counts()
    ratio = (
        sev_counts.max() / sev_counts.min() if sev_counts.min() else float("inf")
    )

    segmented = segment_park(eq)
    seg_cov = (
        segmented.groupby("segment_id")
        .agg(n=("equipment_id", "count"), inst=("instrumented", "sum"))
        .assign(coverage=lambda f: (f["inst"] / f["n"]).round(4))
    )

    align = alignment_rate(ev, sensors)

    questions = [
        {
            "question": "Peut-on modéliser le parc SITE-OUEST par les capteurs ?",
            "chiffre": f"SITE-OUEST : {int(by_site.loc['SITE-OUEST','inst']) if 'SITE-OUEST' in by_site.index else 0} équipement(s) instrumenté(s) sur {int(by_site.loc['SITE-OUEST','n']) if 'SITE-OUEST' in by_site.index else 0}",
            "reponse": "non — population absente côté capteurs",
        },
        {
            "question": "Peut-on détecter les événements critical avec fiabilité capteur ?",
            "chiffre": f"taux rapprochement critical : {align.loc[align.severity=='critical','rate'].iloc[0] if 'critical' in align['severity'].values else 0}",
            "reponse": "non — effectifs et couverture insuffisants",
        },
        {
            "question": "Peut-on inférer une tendance inter-capteurs sur tout le parc ?",
            "chiffre": f"couverture globale : {round(len(inst)/len(eq),4)} — ratio sévérité max/min : {round(ratio,1)}",
            "reponse": "non — grain et représentativité inadaptés",
        },
    ]

    return {
        "equipment_total": int(len(eq)),
        "instrumented": int(len(inst)),
        "coverage_rate": round(len(inst) / len(eq), 4),
        "by_site": by_site.reset_index().to_dict(orient="records"),
        "by_criticality": by_crit.reset_index().to_dict(orient="records"),
        "severity_imbalance_ratio": round(float(ratio), 2),
        "alignment_by_severity": align.to_dict(orient="records"),
        "segmentation": {
            "n_clusters": 4,
            "variables": ["age_years", "rated_power_kw", "criticality", "site_id", "equipment_type"],
            "coverage_by_segment": seg_cov.reset_index().to_dict(orient="records"),
        },
        "three_unanswerable_questions": questions,
    }
