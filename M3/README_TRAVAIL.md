# DiagOps M3 — Espace de travail

Pipeline multi-source (tables M2 + capteurs).  
**Règle :** ne pas intégrer de relevés suspects dans `output/processed/` sans audit.

## Se placer

```bash
cd work/M3
# pwd doit finir par .../work/M3
```

## Installation

```bash
# Python 3.13 recommandé (wheels scipy/pandas)
/usr/local/bin/python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
PYTHONPATH=. python -m pytest -q
```

## Étape 1 — Audit capteurs (avant intégration)

```bash
source .venv/bin/activate
PYTHONPATH=. python scripts/audit_sensors.py --output ./output/audit
```

Sorties dans `output/audit/` :
- `sensor_audit_report.md` — synthèse
- `sensor_findings.csv` — anomalies (règle, décision)
- `sensor_rows_to_exclude.csv` — lignes à ne pas intégrer telles quelles
- `sensor_rows_ok_candidate.csv` — candidats sains (pas encore processed)

Décisions : `quarantine` / `block` / `hold_for_review` → exclusion ; `info` → tracé seulement.

## Étape 2 — Pipeline multi-source (après arbitrage)

```bash
source .venv/bin/activate
PYTHONPATH=. python -m src.data_pipeline \
  --input ../../data_pack/2026-S1 \
  --output ./output \
  --m2-processed ../M2/output/processed
```

Ou : `python3 launch.py` → `[1]` audit, `[2]` pipeline.

Sorties :
- `output/processed/` — 4 tables (M2 reprise + capteurs préparés)
- `output/quarantine.csv` — unifiée M2 + capteurs
- `output/aggregates/by_equipment_sensor.csv`
- `output/alignment/measures_events.csv`
- `output/validation_report.json` — décision M4
- `docs/` — diagnostic, couverture, flux

**Décision actuelle :** `utilisable sous conditions` (couverture ~8,5 % du parc).

## Brief online — Base de données

```bash
source .venv/bin/activate
PYTHONPATH=. python scripts/db_workflow.py --reset
# ou : python3 launch.py → [6]
```

- Migrations : `alembic/versions/` (001 M2, 002 capteurs)
- Modèles : `src/db/models.py`
- Résultats requêtes : `output/db/query_results.json`
- Doc : `docs/db_online.md`

Les fichiers de `data_pack/` ne sont **jamais** modifiés.
