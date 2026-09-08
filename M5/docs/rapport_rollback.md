# Rapport de rollback — DiagOps M5

**Date d'exercice :** 2026-09-07  
**Environnement :** labo local (`work/M5`, Compose + artefacts locaux)

| Champ | Valeur |
|---|---|
| Version saine initiale | `diagops-m4-reference-r1` |
| Version candidate | `learner-candidate-v2-degraded` (index simulé dégradé) |
| Motif de restauration | Régression contrôlée / démonstration gate + rollback |
| Début de détection | Injection `faults.json` (`index_valid=false`) → `/health/ready` **503** ; métrique `diagops_index_valid 0` |
| Décision | Restaurer explicitement `diagops-m4-reference-r1` (pas de sélection implicite) |
| Commande | `python3 pipelines/rollback_release.py diagops-m4-reference-r1 --current artifacts/current.json --history artifacts/history` |
| Fin de restauration | `artifacts/current.json` → `release_id=diagops-m4-reference-r1` |
| Objectif de reprise | RTO labo &lt; 10 min (exécuté en &lt; 1 min hors rebuild image) |
| Tests après restauration | `pytest` 8/8 ; `/health/ready` 200 sur API Compose (référence manifeste data_pack) |
| Traces / versions | History : `artifacts/history/diagops-m4-reference-r1.json` ; digests images dans `docs/contrat_versions.md` |
| Écarts et actions | La première promotion n'archivait pas la référence (current absent) → **toujours** seed/archiver la saine avant promo ; gates bad prouvés (`promote` refusé si `status!=passed`) |

## Chronologie condensée

1. Build index candidat local (7 docs, idempotent).
2. Gate `passed` via `ci_local.sh` ; gate `failed` sur candidat bad → promote refusé.
3. Compose up ; Prometheus scrape `api:8000` = `up`.
4. Faute labo index → 503 ; clear faute → 200.
5. Promote dégradé v2 → rollback vers `diagops-m4-reference-r1`.
