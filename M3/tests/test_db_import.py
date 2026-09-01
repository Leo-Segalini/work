"""Tests import DB — idempotence capteurs."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import func, select

from src.db.import_sources import import_equipment, import_measurements
from src.db.models import Base, SensorReading
from src.db.session import build_engine, build_session_factory


@pytest.fixture()
def session(tmp_path):
    db = tmp_path / "test.db"
    engine = build_engine(f"sqlite+pysqlite:///{db}")
    Base.metadata.create_all(engine)
    factory = build_session_factory(engine)
    sess = factory()
    yield sess
    sess.close()


def test_import_measurements_is_idempotent(session, tmp_path: Path):
    eq_csv = tmp_path / "equipment.csv"
    eq_csv.write_text(
        "equipment_id,equipment_type,site_id,commissioning_date,criticality,manufacturer,rated_power_kw\n"
        "EQ-A,pump,SITE-NORD,2014-01-01,high,,45\n",
        encoding="utf-8",
    )
    import_equipment(session, eq_csv)
    session.commit()

    sensors = tmp_path / "sensors.csv"
    sensors.write_text(
        "equipment_id,timestamp,timestamp_utc,sensor_name,value,unit,period\n"
        "EQ-A,2026-01-02T00:00:00Z,2026-01-02T00:00:00Z,temperature_c,40.0,°C,2026-S1\n"
        "EQ-A,2026-01-02T00:00:00Z,2026-01-02T00:00:00Z,temperature_c,40.0,°C,2026-S1\n",
        encoding="utf-8",
    )

    r1 = import_measurements(session, sensors)
    session.commit()
    r2 = import_measurements(session, sensors)
    session.commit()

    assert r1.read == 2
    assert r1.inserted == 1
    assert r1.skipped == 1
    assert r2.inserted == 0
    assert r2.skipped == 2
    count = session.scalar(select(func.count()).select_from(SensorReading))
    assert count == 1
