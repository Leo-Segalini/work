# Remédiation — Brief 2 M4

## Correction principale retenue

**Politique retrieval lexical-first** avec repli vectoriel si score lexical < 2,0.

### Constats avant correction

| Métrique | Vector seul | Lexical-first |
|---|---:|---:|
| recall@k (calibration) | 1,0 | 1,0 |
| Latence moyenne | ~2 374 ms | ~0,56 ms |

### Écarts traités

- Latence vectorielle inacceptable pour usage interactif sans gain recall@k.

### Non-régression

- 18 tests pytest OK
- Citations et abstentions inchangées sur calibration

### Fichiers modifiés

- `src/brief2/correction.py` — logique lexical-first
- `docs/matrice_decision.md` — décision révisée

## Résultats avant / après

Voir `results/brief2/correction_retrieval.json`.
