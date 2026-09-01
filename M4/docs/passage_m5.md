# Passage de relais M4 → M5

**Date :** 2026-08-31  
**Statut M4 :** clôturé côté autonomie — validation test formateur en attente

---

## État figé transmis

| Composant | Chemin | Version / empreinte |
|---|---|---|
| Modèle capteur retenu | Random Forest | `results/benchmark_modele.json` |
| Features | règles M3 + capteur | `src/features.py` |
| RAG production | lexical-first | `src/brief2/correction.py` |
| Embeddings (repli) | all-MiniLM-L6-v2 | `configs/retrieval.yaml` |
| Agent | 3 actions | `src/bounded_agent.py` |
| Protocole | gel window_id | `docs/protocole_evaluation.md` |
| Threat model | 6+7 cas | `docs/threat_model.md` |
| Veille | M0–M4 | `veille_diagops/` |

## Décisions ouvertes pour M5

1. **Déploiement** — containeriser API RAG + modèle RF ; pas de modification silencieuse des baselines.
2. **Monitoring** — tracer abstentions, citations invalides, dérive F1 provenance.
3. **Journalisation** — conserver traces agent (action, query, document_ids).
4. **Rollback** — pouvoir revenir à baseline M3 seule en cas de régression.
5. **AI Act** — valider juridiquement le scénario superviseur (point ouvert veille).

## Conditions non levées

- Oracle `sensor_test.csv` non distribué
- Oracle questions RAG test scellées
- Lot contradiction brief 2 formateur
- Reproduction **pair** brief 2 (grille auto : `approfondissement/grille_reproduction.md`)

## Commandes de rejeu M4

```bash
cd work/M4 && source .venv/bin/activate
PYTHONPATH=. python scripts/run_pipeline.py
PYTHONPATH=. python scripts/run_brief2.py
PYTHONPATH=. python scripts/run_reproduction_grille.py
PYTHONPATH=. python -m pytest -q
```

## Exigences testables pour M5 (proposées)

- [ ] Gate CI : pytest + run_pipeline sans régression F1 calibration > 0.75
- [ ] Latence RAG p95 < 100 ms (lexical-first)
- [ ] 100 % réponses documentaires avec citation valide ou abstention
- [ ] Aucune action agent hors liste autorisée
