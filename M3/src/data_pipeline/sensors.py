"""Préparation des relevés capteurs avec arbitrage tracé.

Aucune ligne suspecte n'entre dans `processed` sans décision explicite.
Les fichiers de `data_pack/` ne sont jamais modifiés.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from contracts.schemas import EXPECTED_SENSOR_UNITS, SENSOR_VALUE_RANGES, SENSOR_NAME_ALIASES
from src.data_pipeline.quarantine import measurement_identifier, quarantine_frame
from src.data_pipeline.timeseries import to_utc

SENTINELS = {-9999.0, -999.0, 9999.0, 99999.0}

# Conversions d'unité déterministes (arbitrages documentés).
UNIT_CONVERSIONS = {
    # (sensor_name_canonique, unit_observée) -> (facteur_multiplicatif, offset_additif, unit_cible)
    ("pressure_bar", "kPa"): (0.01, 0.0, "bar"),  # 1 kPa = 0.01 bar
    ("temperature_c", "K"): (1.0, -273.15, "°C"),
}


def _record(
    source_file: str,
    row_identifier: str,
    rule_id: str,
    column: str,
    observed_value: Any,
    reason: str,
    decision: str,
) -> dict[str, Any]:
    return {
        "source_file": source_file,
        "row_identifier": row_identifier,
        "rule_id": rule_id,
        "column": column,
        "observed_value": "" if observed_value is None else str(observed_value),
        "reason": reason,
        "decision": decision,
    }


def prepare_sensors(
    sensors: pd.DataFrame,
    known_equipment_ids: set[str],
    source_file: str = "sensor_readings.csv",
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:
    """Normalise, quarantine et retourne les mesures préparées.

    Retourne ``(processed, quarantine, stats)``.
    """
    if sensors.empty:
        return sensors.copy(), quarantine_frame([]), {"input": 0, "kept": 0, "excluded": 0}

    work = sensors.copy()
    work["_orig_idx"] = work.index
    work["_row_id"] = measurement_identifier(work)
    work["_value"] = pd.to_numeric(work["value"], errors="coerce")
    work["_ts"] = to_utc(work["timestamp"])
    work["_sensor"] = work["sensor_name"].astype("string")
    work["_unit"] = work["unit"].astype("string")

    records: list[dict[str, Any]] = []
    drop_ids: set[str] = set()

    # Alias de nom (ex. TEMPERATURE_C → temperature_c)
    for idx, row in work.iterrows():
        alias = SENSOR_NAME_ALIASES.get(str(row["_sensor"]))
        if alias and alias != row["_sensor"]:
            records.append(
                _record(
                    source_file,
                    row["_row_id"],
                    "SEN-NAME-001",
                    "sensor_name",
                    row["_sensor"],
                    f"alias normalisé vers {alias}",
                    "valeur_normalisee",
                )
            )
            work.at[idx, "_sensor"] = alias
            work.at[idx, "sensor_name"] = alias

    # Valeurs non numériques
    for _, row in work.loc[work["_value"].isna() & work["value"].notna()].iterrows():
        records.append(
            _record(
                source_file,
                row["_row_id"],
                "SEN-VAL-001",
                "value",
                row["value"],
                "valeur non numérique",
                "exclue",
            )
        )
        drop_ids.add(row["_row_id"])

    # Horodatages illisibles
    for _, row in work.loc[work["_ts"].isna() & work["timestamp"].notna()].iterrows():
        records.append(
            _record(
                source_file,
                row["_row_id"],
                "SEN-TS-001",
                "timestamp",
                row["timestamp"],
                "horodatage illisible",
                "exclue",
            )
        )
        drop_ids.add(row["_row_id"])

    # Capteur hors contrat
    for _, row in work.iterrows():
        if row["_row_id"] in drop_ids:
            continue
        if str(row["_sensor"]) not in EXPECTED_SENSOR_UNITS:
            records.append(
                _record(
                    source_file,
                    row["_row_id"],
                    "SEN-NAME-002",
                    "sensor_name",
                    row["_sensor"],
                    "nom de capteur hors contrat",
                    "exclue",
                )
            )
            drop_ids.add(row["_row_id"])

    # Conversion d'unité + cohérence
    for idx, row in work.iterrows():
        if row["_row_id"] in drop_ids:
            continue
        sensor = str(row["_sensor"])
        unit = str(row["_unit"])
        expected = EXPECTED_SENSOR_UNITS.get(sensor)
        conv = UNIT_CONVERSIONS.get((sensor, unit))
        if conv is not None and pd.notna(row["_value"]):
            factor, offset, target_unit = conv
            new_val = float(row["_value"]) * factor + offset
            records.append(
                _record(
                    source_file,
                    row["_row_id"],
                    "SEN-UNIT-001",
                    "unit",
                    f"{unit}:{row['_value']}",
                    f"conversion déterministe → {target_unit} ({factor}x + {offset})",
                    "valeur_normalisee",
                )
            )
            work.at[idx, "_value"] = new_val
            work.at[idx, "_unit"] = target_unit
            work.at[idx, "unit"] = target_unit
            work.at[idx, "value"] = new_val
        elif expected is not None and unit != expected:
            records.append(
                _record(
                    source_file,
                    row["_row_id"],
                    "SEN-UNIT-002",
                    "unit",
                    f"{sensor}={unit}",
                    f"unité incompatible (attendu {expected}), pas de conversion sûre",
                    "exclue",
                )
            )
            drop_ids.add(row["_row_id"])

    # Sentinelles
    for _, row in work.iterrows():
        if row["_row_id"] in drop_ids or pd.isna(row["_value"]):
            continue
        if float(row["_value"]) in SENTINELS:
            records.append(
                _record(
                    source_file,
                    row["_row_id"],
                    "SEN-SENT-001",
                    "value",
                    row["_value"],
                    "valeur sentinelle",
                    "exclue",
                )
            )
            drop_ids.add(row["_row_id"])

    # Plages physiques (après conversion)
    for _, row in work.iterrows():
        if row["_row_id"] in drop_ids or pd.isna(row["_value"]):
            continue
        bounds = SENSOR_VALUE_RANGES.get(str(row["_sensor"]))
        if bounds is None:
            continue
        lo, hi = bounds
        val = float(row["_value"])
        if not (lo <= val <= hi):
            records.append(
                _record(
                    source_file,
                    row["_row_id"],
                    "SEN-RANGE-001",
                    "value",
                    val,
                    f"hors plage plausible [{lo}, {hi}]",
                    "exclue",
                )
            )
            drop_ids.add(row["_row_id"])

    # FK équipement
    for _, row in work.iterrows():
        if row["_row_id"] in drop_ids:
            continue
        if str(row["equipment_id"]) not in known_equipment_ids:
            records.append(
                _record(
                    source_file,
                    row["_row_id"],
                    "SEN-FK-001",
                    "equipment_id",
                    row["equipment_id"],
                    "équipement absent de la table préparée M2",
                    "exclue",
                )
            )
            drop_ids.add(row["_row_id"])

    # Doublons de clé (sur clés normalisées)
    remaining = work.loc[~work["_row_id"].isin(drop_ids)].copy()
    remaining["_key"] = (
        remaining["equipment_id"].astype(str)
        + "|"
        + remaining["timestamp"].astype(str)
        + "|"
        + remaining["_sensor"].astype(str)
    )
    for key, group in remaining.groupby("_key", sort=False):
        if len(group) < 2:
            continue
        values = group["_value"].dropna().round(6).unique()
        if len(values) <= 1:
            # garder la première, supprimer les copies exactes
            keep_idx = group.index[0]
            for idx, row in group.iterrows():
                if idx == keep_idx:
                    continue
                records.append(
                    _record(
                        source_file,
                        row["_row_id"],
                        "SEN-DUP-001",
                        "value",
                        row.get("value"),
                        "doublon strict de clé logique",
                        "doublon_supprime",
                    )
                )
                drop_ids.add(row["_row_id"])
        else:
            for _, row in group.iterrows():
                records.append(
                    _record(
                        source_file,
                        row["_row_id"],
                        "SEN-DUP-002",
                        "value",
                        row.get("value"),
                        f"doublon conflictuel {sorted(map(float, values))}",
                        "exclue",
                    )
                )
                drop_ids.add(row["_row_id"])

    kept = work.loc[~work["_row_id"].isin(drop_ids)].copy()
    kept["value"] = kept["_value"]
    kept["unit"] = kept["_unit"]
    kept["sensor_name"] = kept["_sensor"]
    kept["timestamp_utc"] = kept["_ts"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    # Hypothèse fuseau : valeurs déjà Z ou interprétées UTC (tracée en registre)
    processed_cols = [
        "equipment_id",
        "timestamp",
        "timestamp_utc",
        "sensor_name",
        "value",
        "unit",
        "period",
    ]
    processed = kept.loc[:, [c for c in processed_cols if c in kept.columns]].reset_index(drop=True)

    quarantine = quarantine_frame(records) if records else quarantine_frame([])
    stats = {
        "input": int(len(work)),
        "kept": int(len(processed)),
        "excluded": int(len(drop_ids)),
        "quarantine_records": int(len(quarantine)),
    }
    return processed, quarantine, stats
