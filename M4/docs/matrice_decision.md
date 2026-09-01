# Matrice de décision M4

| Dimension | Baseline M3 | Modèle random_forest | RAG vectoriel |
|---|---|---|---|
| Qualité (F1 cal.) | 0.37422 | 0.782609 | recall@k 1.0 |
| Robustesse | règles figées | features + règles | citations vérifiables |
| Latence | 0.0008 ms/ligne | 0.0653 ms/ligne | 1979.22 ms/q |
| Réversibilité | haute | haute | haute |

## Décision

**adopter sous conditions (test scellé formateur requis)**

Conditions :
- validation formateur sur test scellé ;
- provenance synthétique M3 documentée — pas de conclusion parc entier ;
- agent limité à une action, sans effet externe.
