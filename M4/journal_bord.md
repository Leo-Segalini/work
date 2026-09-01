# Journal de bord — M4

## Init — 2026-08-31

- `python tools/init_module.py M4` → `work/M4/`
- venv Python 3.13 + `requirements.lock`

## Brief 1 présentiel

| Date | Activité | Preuve |
|---|---|---|
| 2026-08-31 | Validation contrats manifeste + questions | `src/io_contracts.py` |
| 2026-08-31 | Baseline M3 + features (règles + capteur) | `src/baseline_m3.py`, `src/features.py` |
| 2026-08-31 | Benchmark modèles LR vs RF vs baseline | `results/benchmark_modele.json` |
| 2026-08-31 | Retrieval none / lexical / vectoriel | `results/benchmark_retrieval.json` |
| 2026-08-31 | RAG cité + agent borné | `src/rag_pipeline.py`, `src/bounded_agent.py` |
| 2026-08-31 | Threat model + checks | `docs/threat_model.md`, `src/threats.py` |
| 2026-08-31 | Veille M0–M4 consolidée | `veille_diagops/` |

## Résultats clés (calibration)

| Système | F1 (fabriquée) |
|---|---:|
| Baseline M3 (règles) | 0,374 |
| Random Forest (retenu) | 0,783 |
| RAG vectoriel recall@k | 1,0 (calibration) |

**Décision provisoire :** adopter modèle + RAG **sous conditions** — validation test scellé formateur requise.

## Commandes

```bash
cd work/M4 && source .venv/bin/activate
PYTHONPATH=. python scripts/run_pipeline.py
PYTHONPATH=. python -m pytest -q
python launch.py
```

**Interface explorateur :** `streamlit run ui/explorer_app.py` ou `launch.py` option 6.

## Brief online — 2026-08-31

- `docs/dossier_conception_m4.md` — besoin, comparaison familles, recommandation CampusAtlas
- `docs/tableau_donnees_necessaires.md`, `registre_risques_online.md`

## Brief 2 — 2026-08-31

| Activité | Preuve |
|---|---|
| Audit transmissibilité | `src/brief2/audit.py` |
| Qualification lots test | `approfondissement/qualification_nouveau_lot.md` |
| Correction lexical-first | latence ~2374 ms → ~0,56 ms |
| Menaces étendues (7 cas) | `src/brief2/extended_threats.py` |
| Défense | `approfondissement/defense.md` |

**Commande :** `PYTHONPATH=. python scripts/run_brief2.py` (option 7)

## Limites ouvertes

- Métriques test capteur : oracle scellé (formateur).
- RAG extractif (pas LLM génératif) — suffisant M4, extension M5+.
- Reproduction par **pair** (phase 2 brief 2) : à faire en présentiel.
- Lot contradiction formateur : hors dépôt apprenant.
