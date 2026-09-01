"""Import des sources DiagOps en base — idempotent pour les capteurs."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import Equipment, Event, Maintenance, SensorReading


@dataclass
class ImportReport:
    table: str
    read: int = 0
    inserted: int = 0
    skipped: int = 0
    rejected: int = 0
    reasons: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "table": self.table,
            "read": self.read,
            "inserted": self.inserted,
            "skipped": self.skipped,
            "rejected": self.rejected,
            "reasons": dict(sorted(self.reasons.items())),
        }


def read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def optional_date(value: str) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def optional_float(value: str) -> float | None:
    if value in ("", None):
        return None
    return float(value)


def parse_datetime(value: str) -> datetime:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return ts.to_pydatetime()


def _reject(report: ImportReport, reason: str) -> None:
    report.rejected += 1
    report.reasons[reason] = report.reasons.get(reason, 0) + 1


def import_equipment(session: Session, path: Path) -> ImportReport:
    report = ImportReport(table="equipment")
    for row in read_rows(path):
        report.read += 1
        try:
            with session.begin_nested():
                session.add(
                    Equipment(
                        equipment_id=row["equipment_id"],
                        equipment_type=row["equipment_type"],
                        site_id=row["site_id"],
                        commissioning_date=optional_date(row["commissioning_date"]),
                        criticality=row["criticality"],
                        manufacturer=row["manufacturer"] or None,
                        rated_power_kw=optional_float(row["rated_power_kw"]),
                    )
                )
            report.inserted += 1
        except IntegrityError as error:
            _reject(report, type(error.orig).__name__ if error.orig else "IntegrityError")
        except (KeyError, ValueError) as error:
            _reject(report, type(error).__name__)
    return report


def import_events(session: Session, path: Path) -> ImportReport:
    report = ImportReport(table="events")
    for row in read_rows(path):
        report.read += 1
        try:
            end_at = parse_datetime(row["end_at"]) if row.get("end_at") else None
            with session.begin_nested():
                session.add(
                    Event(
                        event_id=row["event_id"],
                        equipment_id=row["equipment_id"],
                        start_at=parse_datetime(row["start_at"]),
                        end_at=end_at,
                        event_type=row["event_type"],
                        severity=row["severity"],
                        period=row["period"],
                    )
                )
            report.inserted += 1
        except IntegrityError as error:
            _reject(report, type(error.orig).__name__ if error.orig else "IntegrityError")
        except (KeyError, ValueError) as error:
            _reject(report, type(error).__name__)
    return report


def import_maintenance(session: Session, path: Path) -> ImportReport:
    report = ImportReport(table="maintenance_history")
    for row in read_rows(path):
        report.read += 1
        try:
            closed = parse_datetime(row["closed_at"]) if row.get("closed_at") else None
            with session.begin_nested():
                session.add(
                    Maintenance(
                        maintenance_id=row["maintenance_id"],
                        event_id=row["event_id"],
                        equipment_id=row["equipment_id"],
                        opened_at=parse_datetime(row["opened_at"]),
                        closed_at=closed,
                        intervention_type=row["intervention_type"],
                        outcome=row["outcome"],
                        downtime_minutes=int(float(row["downtime_minutes"])),
                        labor_hours=optional_float(row.get("labor_hours", "")),
                        parts_cost_eur=optional_float(row.get("parts_cost_eur", "")),
                        parts_replaced_count=int(float(row["parts_replaced_count"])),
                        work_order_note=row.get("work_order_note") or "",
                        period=row["period"],
                    )
                )
            report.inserted += 1
        except IntegrityError as error:
            _reject(report, type(error.orig).__name__ if error.orig else "IntegrityError")
        except (KeyError, ValueError) as error:
            _reject(report, type(error).__name__)
    return report


def import_measurements(session: Session, path: Path) -> ImportReport:
    """Import idempotent : ON CONFLICT DO NOTHING sur la clé logique."""
    report = ImportReport(table="sensor_readings")
    for row in read_rows(path):
        report.read += 1
        try:
            ts_raw = row.get("timestamp") or row.get("timestamp_utc", "")
            ts = parse_datetime(row.get("timestamp_utc") or row["timestamp"])
            payload = {
                "equipment_id": row["equipment_id"],
                "timestamp": ts,
                "timestamp_raw": ts_raw,
                "sensor_name": row["sensor_name"],
                "value": float(row["value"]),
                "unit": row["unit"],
                "period": row["period"],
            }
            stmt = sqlite_insert(SensorReading).values(**payload)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=["equipment_id", "timestamp", "sensor_name"]
            )
            result = session.execute(stmt)
            if result.rowcount:
                report.inserted += 1
            else:
                report.skipped += 1
        except IntegrityError as error:
            name = type(error.orig).__name__ if error.orig else "IntegrityError"
            if "FOREIGN KEY" in str(error.orig).upper():
                _reject(report, "ForeignKeyViolation")
            else:
                _reject(report, name)
        except (KeyError, ValueError) as error:
            _reject(report, type(error).__name__)
    return report


def import_all_m2(session: Session, processed_dir: Path) -> list[ImportReport]:
    """Ordre FK : equipment → events → maintenance."""
    reports = [
        import_equipment(session, processed_dir / "equipment.csv"),
        import_events(session, processed_dir / "events.csv"),
        import_maintenance(session, processed_dir / "maintenance_history.csv"),
    ]
    return reports
