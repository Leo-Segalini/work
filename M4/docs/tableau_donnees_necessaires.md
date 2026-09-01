# Tableau des données nécessaires — M4

| Besoin | Source | Disponible | Manquant | Pertinence | Droits / confidentialité | Volume minimal |
|---|---|:---:|:---:|---|---|---|
| Provenance capteur (calibration) | `model_eval/sensor_calibration.csv` | ✅ | — | Cible directe | Formation interne | 900 lignes OK |
| Provenance capteur (test) | `model_eval/sensor_test.csv` | ✅ | Labels oracle | Évaluation gelée | Formation | 1800 lignes OK |
| Règles baseline | `reference_runs/m3_for_m4/` | ✅ | — | Plancher | Public formation | — |
| Corpus procédures | `knowledge/` + manifeste | ✅ | — | RAG | Rôles par document | 8 docs OK |
| Questions RAG cal. | `rag_eval/questions.jsonl` | ✅ | — | Réglage retrieval | — | 12 OK |
| Questions RAG test | `rag_eval/questions.jsonl` | ✅ | Labels scellés | Test gelé | — | 12 OK |
| Mesures parc complet | M3 `processed/` | ✅ | Couverture 8,5 % | Contexte limite | Interne | Non suffisant seul |
| Lot contradiction B2 | Canal formateur | ❌ | Lot caché post-gel | Robustesse | — | — |

## Biais et validité

- Données **synthétiques** — DATA_CARD interdit conclusions industrielles directes.
- Fenêtres **indivisibles** — pas de mélange train/test intra-fenêtre.
- SITE-OUEST synthétique M3 — ne pas confondre avec mesure réelle.
