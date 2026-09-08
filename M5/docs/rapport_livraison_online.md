# Brief online M5 — Livrables

**Date :** 2026-09-07  
**Artefact de référence :** release `diagops-m4-reference-r1` (RAG extractif pédagogique)  
**Environnements :** préproduction labo = Compose local ; production = **non ouverte** (décision humaine requise).

## 1. Artefact

| Élément | Valeur |
|---|---|
| Entrées | manifeste knowledge + documents `data_pack` ; manifeste de release |
| Sorties | `/health/*`, `/version`, `/metrics` ; index candidat ; gate_report |
| Paramètres | `DIAGOPS_REFERENCE_MANIFEST`, `DIAGOPS_FAULT_FILE` |
| Dépendances | FastAPI, uvicorn, Prometheus, Docker |
| Version saine | `diagops-m4-reference-r1` |
| Résultats de référence | `evaluation/metrics_calibration.json` (hit@3 = 1.0 côté check M5) |

Détail des empreintes : `docs/contrat_versions.md`.

## 2. Conteneurisation

- `deploy/Dockerfile` (Python 3.12.11-slim, user non-root 65532)
- `deploy/compose.yaml` : services `indexer`, `api`, `prometheus`
- Healthcheck API sur `/health/ready`
- Smoke :

```bash
docker compose -f deploy/compose.yaml up --build -d
curl -s http://127.0.0.1:8000/health/ready
```

## 3. Versionnement

Déclenche une **nouvelle** version : code, corpus, index, prompt, modèle, gates.  
Peut rester inchangé : Prometheus tag épinglé tant que le digest est journalisé.  
Registre : `docs/contrat_versions.md` + `artifacts/current.json` / `history/`.

## 4. CI / validation

Script : `pipelines/ci_local.sh`

1. `pytest`
2. `build_index` → candidat
3. `evaluate_release` → `gate_report.json`
4. **Stop** si `status != passed`
5. Promotion = commande manuelle `promote_release.py` (pas d'auto-prod)

Preuve négative : candidat `artifacts/candidates/bad/` → promote refusé.

## 5. Monitoring

Tableau opérationnel : `monitoring/metrics.md`  
UI Prometheus labo : http://127.0.0.1:9090 (cible `diagops-api` = `up`)  
Export / notes dashboard : `monitoring/dashboards/README.md`

## 6. Livraison candidate + restauration

| Étape | Preuve |
|---|---|
| Candidat indexé | `artifacts/candidates/local/index.json` |
| Gate | `gate_report.json` status `passed` |
| Promo dégradée contrôlée | `learner-candidate-v2-degraded` |
| Rollback | `diagops-m4-reference-r1` restauré |
| Rapport | `docs/rapport_rollback.md` |
| Procédure | `docs/runbook.md` |

## Critères brief online — checklist

- [x] Artefact reconstruisible (Compose + requirements.lock)
- [x] Évaluation = gate de livraison
- [x] Métriques reliées à une décision (seuils + actions)
- [x] Modèle / données / index versionnés
- [x] Préprod ≠ prod (prod non auto)
- [x] Restauration vérifiable
