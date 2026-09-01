# Protocole d'évaluation M4

- **Date de gel :** 2026-08-31
- **Graine :** 20260831
- **Cible :** provenance capteur (`réelle` / `fabriquée`) — pas prédiction de panne
- **Groupe :** `window_id` (30 mesures/fenêtre, split GroupShuffleSplit 80/20)
- **Calibration :** `sensor_calibration.csv` (900 lignes, 30 fenêtres)
- **Test scellé :** `sensor_test.csv` (1800 lignes) — oracle formateur

## Seuils d'acceptation (calibration)

| Métrique | Baseline M3 | Modèle retenu (random_forest) |
|---|---:|---:|
| F1 fabriquée | 0.37422 | 0.782609 |
| Recall | 0.272727 | 0.681818 |
| Precision | 0.596026 | 0.918367 |

## RAG

- Embedding : `sentence-transformers/all-MiniLM-L6-v2`
- Stratégies : none, lexical, vector
- Abstention si `answerable=false` ou preuves insuffisantes
