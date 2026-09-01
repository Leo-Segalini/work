# Recommandations d'architecture M4

1. **Geler** protocole et splits avant tout benchmark test.
2. **Conserver** baseline M3 comme plancher — ne pas déployer un modèle qui régresse en recall sans justification.
3. **RAG extractif cité** avant tout LLM génératif en production.
4. **Agent** : une action, pas de mémoire, pas d'écriture — compatible supervision humaine.
5. **Veille** : checkpoint réglementaire à chaque module M5–M8.

## Exigences vérifiables (tests)

- `test_agent_bounds.py` — 3 actions seulement
- `test_citations.py` — citations résolubles
- `test_abstention.py` — refus sans citation fabriquée
- `threats.run_threat_checks()` — atténuations de base
