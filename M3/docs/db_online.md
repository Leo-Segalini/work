# Brief online M3 — Persistance SQLAlchemy + Alembic

## 1. Modèle de stockage retenu

| Critère | Relationnel (SQLite) | Fichiers Parquet/CSV |
|---|---|---|
| Intégrité FK | **contraintes + rejet explicite** | manuelle à chaque run |
| Idempotence import | **UNIQUE + ON CONFLICT** | diff difficile |
| Requêtes jointures | SQL natif | rechargement complet |
| Volumétrie ~50k mesures | OK pédagogique | OK lecture seule |
| Coût ops | fichier `.db` rejouable | pas de schéma versionné |

**Retenu :** SQLite relationnel pour M2 (faible volume, FK) **et** capteurs (index + unicité).  
**Alternative écartée :** Parquet seul — performant en lecture colonne mais pas de FK ni migrations.

## 2. Workflow

```bash
cd work/M3 && source .venv/bin/activate
PYTHONPATH=. python scripts/db_workflow.py --reset
```

Séquence :
1. `alembic upgrade 001_initial_m2` → tables M2
2. Import CSV préparés (`output/processed/`)
3. `alembic upgrade head` → `sensor_readings`
4. Import capteurs **×2** (démonstration idempotence)

## 3. Migrations

| Revision | Contenu | downgrade |
|---|---|---|
| `001_initial_m2` | equipment, events, maintenance_history | supprime les 3 tables |
| `002_sensor_readings` | capteurs + UNIQUE + index | supprime `sensor_readings` seulement |

Clé logique mesures : `UNIQUE (equipment_id, timestamp, sensor_name)` → violation = ligne ignorée (idempotent).

FK capteurs → equipment : **RESTRICT** — mesure orpheline **rejetée** (comptée).

## 4. Résultats import (dernier run)

| Table | Lues | Insérées | Rejetées |
|---|---:|---:|---:|
| equipment | 411 | 411 | 0 |
| events | 502 | 502 | 0 |
| maintenance | 1738 | 1738 | 0 |
| sensor (passe 1) | 48860 | 48821 | 39 |
| sensor (passe 2) | 48860 | **0** | 39 (skipped 48821) |

Idempotence : **OK** (2ᵉ passe : 0 insertion, 48821 ignorées).

Rejets capteurs : 39 lignes `ValueError` (horodatage/valeur illisible dans le CSV préparé).

## 5. Requêtes

Résultats : `output/db/query_results.json`

- mesures par équipement × capteur
- bornes temporelles par série
- équipements sans mesure (~376/411)
- plan de requête index `ix_sensor_eq_name_ts`

## 6. Apport vs CSV

| | Base | CSV direct |
|---|---|---|
| FK | garanties à l'insert | vérification manuelle |
| Rejeu schéma | Alembic | scripts ad hoc |
| Idempotence | native | diff externe |
| Coût | migration + `.db` | simple mais relecture lourde |

Fichier `.db` **non versionné** — reconstruit via `db_workflow.py --reset`.
