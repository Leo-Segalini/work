# Rapport de capacité — M5

**Date :** 2026-09-07  
**Profil annoncé :** `lab_smoke_sequential_v1`  
**Cible :** API Compose `http://127.0.0.1:8000`  
**Script :** `pipelines/capacity_probe.py`  
**Preuve JSON :** `artifacts/candidates/local/capacity_report.json`

## Profil

| Paramètre | Valeur |
|---|---|
| Type | Séquentiel local (pas de service externe) |
| Endpoints | `/health/live`, `/health/ready`, `/version`, `/metrics` |
| Requêtes | 200 |
| Timeout | 2 s |

## Résultats mesurés

| Métrique | Valeur |
|---|---|
| Durée | 0.196 s |
| Débit | ~1020 req/s |
| Erreurs | 0 (0 %) |
| Latence p50 | 0.78 ms |
| Latence p95 | 1.36 ms |
| Latence max | 20.81 ms |
| Latence mean | 0.98 ms |

## Interprétation

- Sous ce profil léger, l'API santé est loin de saturer.
- **Premier point de saturation hypothétique :** CPU du conteneur API / concurrence
  réelle (GIL) si on passe à du parallelisme élevé ou à du retrieval documentaire
  complet — hors scope du probe santé.
- Limites Compose actuelles : API `mem_limit 512m`, `cpus 1.0`.
- Le profil **n'utilise pas** le split test RAG scellé ni d'oracle formateur.

## Rejeu

```bash
cd work/M5 && source .venv/bin/activate
python3 pipelines/capacity_probe.py --requests 200 \
  --output artifacts/candidates/local/capacity_report.json
```
