# Workflow CI/CD — M5 (préproduction pédagogique)

## Schéma

```text
push / manuel local
        │
        ▼
   pytest -q
        │
        ▼
 build_index → artifacts/candidates/<id>/index.json
        │
        ▼
 evaluate_release → gate_report.json
        │
   status==passed ?
        │ non ──► STOP (pas de promote)
        ▼ oui
  décision humaine
        │
        ▼
 promote_release → artifacts/current.json (+ archive history)
        │
        ▼
 smoke /health/ready + /metrics
        │
   incident ? ──► rollback_release <release_id_sain>
```

## Commandes

```bash
cd work/M5 && source .venv/bin/activate
./pipelines/ci_local.sh
# si passed et décision OK :
python3 pipelines/promote_release.py \
  --candidate artifacts/candidates/local/release.json \
  --gate artifacts/candidates/local/gate_report.json \
  --current artifacts/current.json \
  --history artifacts/history
```

## Environnements

| Env | Rôle | Promotion |
|---|---|---|
| Local / Compose | Préproduction pédagogique | Automatisable jusqu'au gate |
| Production | Hors scope labo M5 | **Toujours** décision humaine + veille à jour |

## GitHub Actions (optionnel)

Non exigé pour le labo si `ci_local.sh` est exécuté et journalisé.
Si ajouté plus tard : job = checkout → setup Python → `ci_local.sh` ;
artefact `gate_report.json` ; **aucun** step `promote` sans `environment: production` + approver.
