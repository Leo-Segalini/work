# Grille de reproduction — M4

**Date :** 2026-08-31
**Mode :** auto-audit (substitut phase 2 en autonomie)

| Vérification | Statut | Preuve |
|---|---|---|
| Environnement + tests (hors brief2 lent) | reproduit | ...............                                                          [100%] \| 15 passed in 0.07s |
| Run principal pipeline M4 | reproduit | "output": "/Users/segalini-briant/Documents/GitHub/atlas-cisia-s04/work/M4/results" \| } |
| Run modèle RF | reproduit | F1=0.782609 |
| Run retrieval | reproduit | {   "generated_at": "2026-08-31T07:21:48.594822+00:00",   "embedding_model": "sentence-transformers/all-MiniLM-L6-v2", |
| Échantillon citations / abstention | reproduit | .....                                                                    [100%] \| 5 passed in 0.01s |
| Menaces (agent + extended) | reproduit | ....                                                                     [100%] \| 4 passed in 0.06s |
| Fuite test | non testé | Oracle capteur/RAG hors dépôt — protocole window_id documenté |
| Hypothèses implicites | écart | Features incluent règles M3 — assumé et documenté |

## Meilleur argument contraire

RF non validé sur test scellé ; lexical-first peut échouer sur requêtes sémantiques pures.

*Phase 2 pair : à compléter par un autre apprenant en présentiel.*
