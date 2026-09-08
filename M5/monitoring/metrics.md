# Contrat de métriques M5

Ne pas inclure le contenu intégral des documents, prompts ou réponses dans les
labels de métriques. Traces : rétention 14 jours labo, accès superviseur uniquement.

| Plan | Métrique | Source | Fréquence | Seuil | Responsable | Action |
|---|---|---|---|---|---|---|
| Service | `diagops_ready` | `/metrics` + Prometheus | 15 s | =0 pendant ≥1 min | Exploitant M5 | Diagnostiquer manifeste/release ; rollback si besoin |
| Service | `diagops_dependency_up` | `/metrics` (fault labo) | 15 s | =0 | Exploitant M5 | Qualifier panne génération ; basculer / attendre ; journaliser |
| Service | HTTP `/health/ready` | Compose healthcheck | 10 s | 503 | Exploitant M5 | Incident readiness → runbook rollback |
| Retrieval | `diagops_index_valid` | `/metrics` | 15 s | =0 | Exploitant M5 | Ne pas promouvoir ; reconstruire index candidat ; gates |
| Retrieval | `document_count` (gate) | `evaluate_release` | chaque candidat | ≥7 | Ingénieur livrable | Bloquer promotion |
| Retrieval | `expected_document_hit_at_3` | métriques calibration M4 | chaque candidat | ≥0.8 | Ingénieur livrable | Bloquer promotion / investiguer corpus |
| Réponse | `citation_resolvable_rate` | gate CI | chaque candidat | =1.0 | Ingénieur livrable | Bloquer ; corriger citations |
| Réponse | `correct_abstention_rate` | gate CI | chaque candidat | =1.0 | Ingénieur livrable | Bloquer ; revoir refus |
| Réponse | autonomie agent | contrat `agent_actions.json` | revue livrable | aucune action hors liste | Lead DiagOps | Refus merge / gate sécurité |

## Injection de laboratoire

Fichier : `artifacts/runtime/faults.json` (monté dans le conteneur API).

```json
{"index_valid": false}
```

Effet attendu : `diagops_index_valid 0` et `/health/ready` → 503.
