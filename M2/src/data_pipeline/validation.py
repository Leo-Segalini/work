"""Contrôles de qualité et règles métier DiagOps M2."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd

from contracts.schemas import (
    CRITICALITIES,
    EVENT_TYPES,
    INTERVENTION_TYPES,
    OUTCOMES,
    SEVERITIES,
)


def missing_required_columns(
    frame: pd.DataFrame, required_columns: Iterable[str]
) -> list[str]:
    """Retourne les colonnes obligatoires absentes, dans un ordre stable."""
    return sorted(set(required_columns) - set(frame.columns))


REQUIRED = {
    "equipment": [
        "equipment_id",
        "equipment_type",
        "site_id",
        "commissioning_date",
        "criticality",
    ],
    "events": [
        "event_id",
        "equipment_id",
        "start_at",
        "event_type",
        "severity",
        "period",
    ],
    "maintenance": [
        "maintenance_id",
        "event_id",
        "equipment_id",
        "opened_at",
        "intervention_type",
        "outcome",
        "downtime_minutes",
        "parts_replaced_count",
        "work_order_note",
        "period",
    ],
}


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


def check_duplicate_ids(
    frame: pd.DataFrame, id_col: str, source_file: str, rule_id: str
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    duplicated = frame[frame[id_col].duplicated(keep=False)]
    for _, row in duplicated.iterrows():
        records.append(
            _record(
                source_file,
                row[id_col],
                rule_id,
                id_col,
                row[id_col],
                "identifiant dupliqué",
                "quarantine",
            )
        )
    return records


def check_domain(
    frame: pd.DataFrame,
    column: str,
    allowed: set[str],
    source_file: str,
    id_col: str,
    rule_id: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if column not in frame.columns:
        return records
    bad = frame[~frame[column].astype(str).isin(allowed) & frame[column].notna()]
    for _, row in bad.iterrows():
        records.append(
            _record(
                source_file,
                row[id_col],
                rule_id,
                column,
                row[column],
                f"valeur hors domaine attendu {sorted(allowed)}",
                "quarantine",
            )
        )
    return records


def check_negative_numeric(
    frame: pd.DataFrame,
    columns: list[str],
    source_file: str,
    id_col: str,
    rule_id: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for column in columns:
        if column not in frame.columns:
            continue
        series = pd.to_numeric(frame[column], errors="coerce")
        bad = frame[series < 0]
        for idx, row in bad.iterrows():
            records.append(
                _record(
                    source_file,
                    row[id_col],
                    rule_id,
                    column,
                    row[column],
                    "valeur numérique négative impossible",
                    "quarantine",
                )
            )
    return records


def check_date_order(
    frame: pd.DataFrame,
    start_col: str,
    end_col: str,
    source_file: str,
    id_col: str,
    rule_id: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if start_col not in frame.columns or end_col not in frame.columns:
        return records
    start = pd.to_datetime(frame[start_col], errors="coerce", utc=True)
    end = pd.to_datetime(frame[end_col], errors="coerce", utc=True)
    mask = end.notna() & start.notna() & (end < start)
    for _, row in frame.loc[mask].iterrows():
        records.append(
            _record(
                source_file,
                row[id_col],
                rule_id,
                end_col,
                f"{row[start_col]} > {row[end_col]}",
                "date de fin antérieure à la date de début",
                "quarantine",
            )
        )
    return records


def check_foreign_keys(
    child: pd.DataFrame,
    child_col: str,
    parent_ids: set[str],
    source_file: str,
    id_col: str,
    rule_id: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    missing = child[~child[child_col].astype(str).isin(parent_ids)]
    for _, row in missing.iterrows():
        records.append(
            _record(
                source_file,
                row[id_col],
                rule_id,
                child_col,
                row[child_col],
                "référence absente dans la table parente",
                "quarantine",
            )
        )
    return records


def run_quality_checks(sources: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    """Exécute les contrôles qualité et retourne des enregistrements de quarantaine."""
    equipment = sources["equipment"]
    events = sources["events"]
    maintenance = sources["maintenance"]
    records: list[dict[str, Any]] = []

    for name, cols in REQUIRED.items():
        missing = missing_required_columns(sources[name], cols)
        if missing:
            records.append(
                _record(
                    f"{name}.csv",
                    "FILE",
                    "REQ-COLS",
                    ",".join(missing),
                    missing,
                    "colonnes obligatoires absentes",
                    "block",
                )
            )

    records.extend(
        check_duplicate_ids(equipment, "equipment_id", "equipment.csv", "EQ-DUP")
    )
    records.extend(check_duplicate_ids(events, "event_id", "events.csv", "EVT-DUP"))
    records.extend(
        check_duplicate_ids(
            maintenance, "maintenance_id", "maintenance_history.csv", "MNT-DUP"
        )
    )

    records.extend(
        check_domain(
            equipment,
            "criticality",
            CRITICALITIES,
            "equipment.csv",
            "equipment_id",
            "EQ-CRIT",
        )
    )
    records.extend(
        check_domain(
            events, "severity", SEVERITIES, "events.csv", "event_id", "EVT-SEV"
        )
    )
    records.extend(
        check_domain(
            events, "event_type", EVENT_TYPES, "events.csv", "event_id", "EVT-TYPE"
        )
    )
    records.extend(
        check_domain(
            maintenance,
            "intervention_type",
            INTERVENTION_TYPES,
            "maintenance_history.csv",
            "maintenance_id",
            "MNT-TYPE",
        )
    )
    records.extend(
        check_domain(
            maintenance,
            "outcome",
            OUTCOMES,
            "maintenance_history.csv",
            "maintenance_id",
            "MNT-OUT",
        )
    )

    records.extend(
        check_negative_numeric(
            equipment,
            ["rated_power_kw"],
            "equipment.csv",
            "equipment_id",
            "EQ-NEG",
        )
    )
    records.extend(
        check_negative_numeric(
            maintenance,
            ["downtime_minutes", "labor_hours", "parts_cost_eur", "parts_replaced_count"],
            "maintenance_history.csv",
            "maintenance_id",
            "MNT-NEG",
        )
    )

    records.extend(
        check_date_order(
            events, "start_at", "end_at", "events.csv", "event_id", "EVT-DATE"
        )
    )
    records.extend(
        check_date_order(
            maintenance,
            "opened_at",
            "closed_at",
            "maintenance_history.csv",
            "maintenance_id",
            "MNT-DATE",
        )
    )

    eq_ids = set(equipment["equipment_id"].astype(str))
    evt_ids = set(events["event_id"].astype(str))
    records.extend(
        check_foreign_keys(
            events, "equipment_id", eq_ids, "events.csv", "event_id", "EVT-FK-EQ"
        )
    )
    records.extend(
        check_foreign_keys(
            maintenance,
            "equipment_id",
            eq_ids,
            "maintenance_history.csv",
            "maintenance_id",
            "MNT-FK-EQ",
        )
    )
    records.extend(
        check_foreign_keys(
            maintenance,
            "event_id",
            evt_ids,
            "maintenance_history.csv",
            "maintenance_id",
            "MNT-FK-EVT",
        )
    )
    return records
