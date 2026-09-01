# DiagOps M2 — Espace de travail

Audit et préparation des tables `equipment` / `events` / `maintenance_history`,  
avec **détection des données sensibles** dans les notes.

## Se placer au bon endroit

```bash
# Depuis la racine du dépôt :
cd work/M2

# Depuis work/M0 ou work/M1 :
cd ../M2
```

`pwd` doit finir par `.../work/M2`.

## Installation

```bash
cd work/M2
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.lock
PYTHONPATH=. python3 -m pytest -q
```

## Lanceur

```bash
cd work/M2
source .venv/bin/activate
python3 launch.py
```

| Choix | Action |
|---|---|
| 1 | Pipeline audit + PII → `output/` + `reports/` |
| 2 | Afficher `reports/pii_findings.md` |
| 3 | Afficher `reports/audit_report.md` (décision M3) |
| 4 | Tests |
| 5–6 | Notebooks audit / stats Atlas |
| 7 | Réexécuter stats + exporter HTML |
| 8 | Afficher `journal_bord.md` |

## Livrables M2 (état)

| Brief | Artefact | Statut |
|---|---|---|
| Présentiel | `output/processed/*.csv`, `quarantine.csv`, `validation_report.json` | OK |
| Présentiel | `reports/audit_report.md` → **utilisable sous conditions** | OK |
| Présentiel | `reports/pii_findings.md` (3 hits) | OK |
| Online | `notebooks/m2_statistiques_atlas.ipynb` (exécuté) | OK |
| Online | `reports/m2_statistiques_atlas.html` + `reports/figures/` | OK |
| Transverse | `journal_bord.md` | OK |

Réexécuter le notebook stats + HTML :

```bash
source .venv/bin/activate
jupyter nbconvert --to notebook --execute notebooks/m2_statistiques_atlas.ipynb --inplace
jupyter nbconvert --to html notebooks/m2_statistiques_atlas.ipynb --output-dir reports --output m2_statistiques_atlas.html
```

## Pipeline manuel

```bash
PYTHONPATH=. python3 -m src.data_pipeline \
  --input ../../data_pack/2026-S1 \
  --output ./output
```

Sorties :
- `output/processed/*.csv` — tables préparées (notes masquées)
- `output/quarantine.csv` — anomalies + PII
- `output/validation_report.json`
- `reports/pii_findings.md`
- `reports/audit_report.md`

Les CSV de `data_pack/` ne sont **jamais** modifiés.
