# Chronologie du game day

Exercice labo **~2 min** (2026-09-07) — injection `index_valid=false`, observation Prometheus, clear.
Preuve brute : `artifacts/candidates/local/timeline_2min.json`

| Horodatage UTC | Observation | Signal | Décision | Responsable | Preuve |
|---|---|---|---|---|---|
| 2026-09-07T05:34:46Z | Baseline saine | ready **200** ; `diagops_ready=1` ; `diagops_index_valid=1` | Démarrer exercice | Apprenant | curl + Prometheus |
| 2026-09-07T05:34:46Z | Faute injectée (`faults.json`) | ready **503** immédiat ; Prometheus encore `index_valid=1` (scrape 15 s) | Chronométrer détection métrique | Apprenant | docker exec + curl |
| 2026-09-07T05:35:01Z | +15 s — détection Prometheus | `diagops_index_valid=0` ; ready 503 | **Détection système OK** (~15 s &lt; 2 min) | Observabilité | query `diagops_index_valid` |
| 2026-09-07T05:35:16Z | +30 s | index_valid=0 ; ready 503 | Maintenir observation | Observabilité | timeline_2min.json |
| 2026-09-07T05:35:31Z | +45 s | index_valid=0 ; ready 503 | — | — | — |
| 2026-09-07T05:35:46Z | +60 s | index_valid=0 ; ready 503 | — | — | — |
| 2026-09-07T05:36:01Z | +75 s | index_valid=0 ; ready 503 | — | — | — |
| 2026-09-07T05:36:16Z | +90 s — clear faute | ready **200** immédiat ; Prometheus encore `index_valid=0` (lag scrape) | Restauration exécutée | Incident commander | unlink faults.json |
| 2026-09-07T05:36:31Z | +105 s — recovery métrique | ready 200 ; `diagops_index_valid=1` | Vérif OK | Exécutant | Prometheus |
| 2026-09-07T05:36:46Z | +120 s — fin fenêtre | tout à 1 ; ready 200 | Clôturer exercice labo | Scribe | recovery_2 |

## Lecture pour le game day

| Objectif | Mesure cet exercice |
|---|---|
| Détection HTTP | **&lt; 1 s** (503 dès injection) |
| Détection Prometheus | **~15 s** (intervalle scrape) |
| Décision / clear | à T+90 s (volontaire) |
| Retour métrique vert | **~15 s** après clear |
| Perte de données | aucune |

**Astuce UI Prometheus :** Graph → plage **Last 5 minutes** → requêtes `diagops_index_valid`, `diagops_ready` — tu verras le créneau bas (0) puis remontée (1).
