# M2 — Aller plus loin : qualification industrialisée

Complément facultatif (~20 h) prolongeant l'audit M2 pour qualifier des livraisons successives sans refaire l'analyse à la main.

## Commandes

```bash
cd work/M2
source .venv/bin/activate

# Qualification locale (rapport + code 0 même si REJECTED)
PYTHONPATH=. python scripts/qualify_candidate.py

# Mode CI — échec explicite sur rejet métier
PYTHONPATH=. python scripts/qualify_candidate.py --strict

# Menu interactif
python launch.py   # option 9
```

## Entrées / sorties

| Rôle | Chemin |
|---|---|
| Socle publié | `data_pack/2026-S1/` (lecture seule) |
| Lot candidat | `data_pack/2026-S1/m2_candidate_release/` |
| Règles | `aller_plus_loin/config/quality_rules.yaml` |
| Rapports | `output/candidate_qualification/` |
| Manifeste | `aller_plus_loin/run_manifest.json` |

## Décision obtenue (lot r2)

**REJECTED** — 16 anomalies bloquantes (doublons, collisions historique, domaines, FK).  
Détail argumenté : `output/candidate_qualification/decision_candidate.md`.

## GitHub Actions

Workflow : `.github/workflows/m2-qualification.yml`

- Job **`socle`** : tests + audit données publiées → doit rester vert.
- Job **`candidate`** : qualification avec `--strict` → rouge attendu sur le lot pédagogique r2.

Les artefacts (`qualification_report.json`, `candidate_findings.csv`) permettent de diagnostiquer un rejet sans relancer le workflow.
