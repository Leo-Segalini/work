# Rapport de reproduction — Brief 2 M4

**Auteur du candidat :** apprenant  
**Relecteur :** auto-audit script (`src/brief2/audit.py`)  
**Date :** 2026-08-31  
**Empreinte :** `results/m4_summary.json` + `results/brief2_summary.json`

| Vérification | Statut | Preuve |
|---|---|---|
| Environnement reconstruit | reproduit | `requirements.lock` + venv Python 3.13 |
| Run principal modèle | reproduit | F1 RF 0,783 — `benchmark_modele.json` |
| Run principal retrieval | reproduit | recall@k 1,0 lexical — `benchmark_retrieval.json` |
| Citations vérifiées | reproduit | `tests/test_citations.py` |
| Trois menaces rejouées | reproduit | `tests/test_brief2.py` + extended_threats |
| Fuite test | non testé | Oracle hors dépôt — revue manuelle protocole |
| Hypothèses implicites | écart | Features incluent règles M3 — documenté |

## Meilleur argument contraire

Le modèle RF pourrait **sur-apprendre** les patterns de fabrication du générateur pédagogique ; sans oracle test, la décision reste **conditionnelle**.

**Note :** la reproduction par un pair (phase 2 brief 2) reste à faire en présentiel avec un autre apprenant.
