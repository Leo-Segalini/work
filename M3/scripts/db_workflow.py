#!/usr/bin/env python3
"""Workflow DB M3 online : migrations → import M2 → migration capteurs → import idempotent → requêtes."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from sqlalchemy import func, select, text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.db.import_sources import (  # noqa: E402
    import_all_m2,
    import_measurements,
)
from src.db.models import Equipment, SensorReading  # noqa: E402
from src.db.session import build_engine, database_url, session_scope  # noqa: E402


def run_alembic(*args: str, db_path: Path | None = None) -> None:
    env = {}
    if db_path:
        env["DIAGOPS_DATABASE_URL"] = f"sqlite+pysqlite:///{db_path.resolve()}"
    subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=ROOT,
        check=True,
        env={**dict(__import__("os").environ), **env},
    )


def run_queries(engine) -> dict:
    results: dict = {}

    with engine.connect() as conn:
        # Q12 : mesures par équipement × capteur
        rows = conn.execute(
            text(
                """
                SELECT equipment_id, sensor_name, COUNT(*) AS n
                FROM sensor_readings
                GROUP BY equipment_id, sensor_name
                ORDER BY n DESC
                LIMIT 10
                """
            )
        ).mappings().all()
        results["measures_by_equipment_sensor_top10"] = [dict(r) for r in rows]

        # Q13 : première / dernière mesure par série
        rows = conn.execute(
            text(
                """
                SELECT equipment_id, sensor_name,
                       MIN(timestamp) AS first_ts,
                       MAX(timestamp) AS last_ts,
                       COUNT(*) AS n
                FROM sensor_readings
                GROUP BY equipment_id, sensor_name
                ORDER BY equipment_id, sensor_name
                LIMIT 10
                """
            )
        ).mappings().all()
        results["series_bounds_sample"] = [dict(r) for r in rows]

        # Q14 : équipements sans mesure
        rows = conn.execute(
            text(
                """
                SELECT e.equipment_id
                FROM equipment e
                LEFT JOIN sensor_readings s ON s.equipment_id = e.equipment_id
                WHERE s.id IS NULL
                LIMIT 20
                """
            )
        ).mappings().all()
        results["equipment_without_measures_count"] = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM equipment e
                LEFT JOIN sensor_readings s ON s.equipment_id = e.equipment_id
                WHERE s.id IS NULL
                """
            )
        ).scalar_one()
        results["equipment_without_measures_sample"] = [r["equipment_id"] for r in rows]

        # Q15 : effet index (requête typique par équipement + capteur + plage)
        eq = conn.execute(
            text("SELECT equipment_id FROM sensor_readings LIMIT 1")
        ).scalar_one_or_none()
        if eq:
            sql = text(
                """
                SELECT COUNT(*), AVG(value)
                FROM sensor_readings
                WHERE equipment_id = :eq AND sensor_name = 'temperature_c'
                  AND timestamp >= '2026-01-01' AND timestamp < '2026-07-01'
                """
            )
            t0 = time.perf_counter()
            conn.execute(sql, {"eq": eq}).one()
            elapsed_ms = (time.perf_counter() - t0) * 1000
            plan = conn.execute(
                text(
                    "EXPLAIN QUERY PLAN "
                    "SELECT value FROM sensor_readings "
                    "WHERE equipment_id = :eq AND sensor_name = 'temperature_c' "
                    "AND timestamp >= '2026-01-01'"
                ),
                {"eq": eq},
            ).all()
            results["index_query"] = {
                "equipment_id": eq,
                "elapsed_ms": round(elapsed_ms, 3),
                "explain_plan": [str(p) for p in plan],
                "index_name": "ix_sensor_eq_name_ts",
            }

    with session_scope(engine) as session:
        total = session.scalar(select(func.count()).select_from(SensorReading))
        results["sensor_readings_total"] = total
        results["equipment_total"] = session.scalar(select(func.count()).select_from(Equipment))

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Workflow DB M3 online")
    parser.add_argument(
        "--processed",
        type=Path,
        default=ROOT / "output" / "processed",
        help="CSV préparés (M2 + capteurs)",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=ROOT / "output" / "diagops.db",
        help="fichier SQLite (reconstruit si --reset)",
    )
    parser.add_argument("--reset", action="store_true", help="supprime la base avant migration")
    args = parser.parse_args()

    processed = args.processed.resolve()
    db_path = args.db.resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    out_dir = ROOT / "output" / "db"
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.reset and db_path.exists():
        db_path.unlink()

    import os

    os.environ["DIAGOPS_DATABASE_URL"] = f"sqlite+pysqlite:///{db_path}"

    print("→ alembic upgrade 001_initial_m2")
    run_alembic("upgrade", "001_initial_m2", db_path=db_path)

    print("→ import M2 tables")
    with session_scope(build_engine()) as session:
        m2_reports = import_all_m2(session, processed)
    for r in m2_reports:
        print(json.dumps(r.as_dict(), ensure_ascii=False))

    print("→ alembic upgrade head (capteurs)")
    run_alembic("upgrade", "head", db_path=db_path)

    print("→ import capteurs (1ère passe)")
    with session_scope(build_engine()) as session:
        rep1 = import_measurements(session, processed / "sensor_readings.csv")
    print(json.dumps(rep1.as_dict(), ensure_ascii=False))

    print("→ import capteurs (2ème passe — idempotence)")
    with session_scope(build_engine()) as session:
        rep2 = import_measurements(session, processed / "sensor_readings.csv")
    print(json.dumps(rep2.as_dict(), ensure_ascii=False))

    engine = build_engine()
    queries = run_queries(engine)
    queries["import_pass1"] = rep1.as_dict()
    queries["import_pass2"] = rep2.as_dict()
    queries["database_url"] = database_url()
    queries["idempotence_ok"] = rep2.inserted == 0 and rep2.skipped == rep1.inserted

    (out_dir / "query_results.json").write_text(
        json.dumps(queries, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(f"\n→ résultats : {out_dir / 'query_results.json'}")
    print(f"   idempotence OK : {queries['idempotence_ok']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
