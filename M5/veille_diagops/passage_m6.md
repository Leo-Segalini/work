# Passage de relais réglementaire M5 → M6

**Date :** 2026-09-07  
**Depuis :** entrée veille M5 (`journal_veille.md`)  
**Vers :** module M6 (outils lecture seule, feedback, amélioration continue)

## Acquis réglementaires / exploitation transmis

- Décision M5 : `appliquer` — contrôles d'exploitation mis à jour (gates, runbook,
  minimisation traces, promotion humaine, rollback).
- Agent : toujours une décision, **aucun** outil à effet.
- Preuves : `docs/rapport_rollback.md`, `docs/contrat_versions.md`, `pipelines/ci_local.sh`.

## Points ouverts (obligatoires avant outils M6)

1. Qualification AI Act du scénario superviseur — responsable conformité.
2. Rétention traces hors labo (14 j ≠ éventuelle obligation longue).
3. Fournisseur d'inférence cloud éventuel — localisation / DPA.
4. Feedback : pas de label automatique depuis les logs.

## Condition de levée

Une entrée M6 datée + contrôle modifié (politique outil, gate, ou refus motivé
d'absence d'impact) avant d'activer tout outil à effet ou toute boucle
d'apprentissage automatique.
