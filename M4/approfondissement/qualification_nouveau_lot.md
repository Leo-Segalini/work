# Qualification du nouveau lot — Brief 2 M4

**Date de révélation :** 2026-08-31 (lots test publics data pack — oracle formateur hors dépôt)

## Identité et checksum

- Capteurs : `data_pack/2026-S1/model_eval/sensor_test.csv` (checksum dans `model_eval/checksums.sha256`)
- RAG : `rag_eval/questions.jsonl` split `test` (12 questions, labels scellés)

## Couverture capteurs test

| Indicateur | Valeur |
|---|---:|
| Lignes | 1 800 |
| Fenêtres | 60 |
| Équipements distincts | 32 |
| Capteurs | current_a 420, pressure_bar 420, vibration 390, temp 390, rpm 180 |

**Différence vs calibration :** plus de fenêtres (60 vs 30), pas de colonne `provenance`.

## RAG test

- 12 questions scellées ; rôles technicien (9), public (2), auditeur (1)
- Tags : unit, missing_evidence, restricted_data, agent_bounds, indirect_injection…
- **Non répondables attendus** (oracle) : missing_evidence, restricted_data, scope

## Décision d'admission

**Utiliser pour évaluation gelée uniquement** — interdit de régler seuils ou hyperparamètres sur ce lot.
