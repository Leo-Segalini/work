# Journal de bord M5

| Date | Travail | Preuve | Décision | Risque ou question ouverte |
|---|---|---|---|---|
| 2026-09-07 | Task 0 — init module | `check_m5_release.py` → `status: ready` ; pytest 8/8 ; `/health/*`, `/version`, `/metrics` OK | Version saine = `diagops-m4-reference-r1` | Warnings Starlette/httpx ; Python 3.14 local vs 3.12 image |
| 2026-09-07 | Task 1 — contrat versions | `docs/contrat_versions.md` rempli (unités + checksums) | Sain figé ; candidats dans `artifacts/candidates/` | Digests Docker complétés en T2 |
| 2026-09-07 | Relais M4 → M5 | `work/M4/docs/passage_m5.md` | Reporter 5 décisions ouvertes (deploy, monitoring, traces, rollback, AI Act) | Oracles test scellés ; AI Act ouvert |
| 2026-09-07 | Task 2 — Compose | `docker compose -f deploy/compose.yaml up --build` ; api healthy ; prom :9090 ; limites mem/cpu | Digests journalisés dans contrat_versions | Port 8000 exclusif (stop uvicorn local avant Compose) |
| 2026-09-07 | Task 3 — index | double `build_index` → `idempotent True` ; 7 docs ; `lexical-dfb8faf0c9b4` | Index candidat hors runtime uniquement | — |
| 2026-09-07 | Task 4 — gates / CI | bad gate `failed` + promote refusé ; `pipelines/ci_local.sh` OK ; promote `learner-candidate-v1` | Pas d'auto-promote ; CI = pytest+index+gate | Étendre gates (latence, injection, secrets) plus tard |
| 2026-09-07 | Task 5 — obs (amorcée) | `monitoring/metrics.md` 3 plans ; faute `index_valid=false` → ready 503 puis clear ; Prometheus target `up` | Seuils + responsables nommés | Grafana optionnel |
| 2026-09-07 | Task 6 — rollback exécuté | promo `learner-candidate-v2-degraded` → rollback `diagops-m4-reference-r1` ; `docs/rapport_rollback.md` | Toujours archiver la saine avant promo | Seed history si current absent |
| 2026-09-07 | Task 7 — veille réglementaire | `veille_diagops/journal_veille.md` ; sources EUR-Lex/CNIL ; contrôles reliés (gates, runbook, métriques) ; `passage_m6.md` | Décision `appliquer` ; pas de qualification juridique définitive | AI Act superviseur + rétention hors labo → M6 |
| 2026-09-07 | Exercice timeline 2 min | Injection index_valid → 503 immédiat ; Prometheus 0 à +15 s ; clear → recovery | Détection &lt; 2 min prouvée ; lag scrape 15 s à documenter | Pour game day officiel : garder Graph « Last 5 minutes » |
