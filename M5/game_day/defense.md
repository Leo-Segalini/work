# Support de défense — Game day M5

## Message en 60 secondes

DiagOps M5 livre une stack RAG **reproductible** : versions liées, index candidat
hors runtime, gates CI bloquants, observabilité service/retrieval/réponse,
promotion humaine et rollback **exécuté** vers `diagops-m4-reference-r1`.

## Arbitrages

| Choix | Pourquoi | Coût / limite |
|---|---|---|
| Compose local 3 services | Séparer index / API / obs sans cloud | Pas de HA |
| Gate sur métriques M4 gelées | Reproductibilité pédagogique | Pas un oracle test scellé |
| Probe capacité séquentiel santé | Mesure annoncée sans stress externe | Saturation réelle non forcée |
| Agent non étendu | Hors périmètre M5 | Outils à effet → M6 |
| Rétention traces 14 j labo | Minimisation | Revoir si prod / haut risque |

## Preuves à montrer

1. `docs/contrat_versions.md` + digests
2. Promote refusé sur gate failed
3. Faute `index_valid` → 503 puis clear
4. `docs/rapport_rollback.md`
5. `docs/rapport_capacite.md`
6. `veille_diagops/journal_veille.md` → contrôles
7. `game_day/plan.md` prêt injection

## Ce qu'on ne prétend pas

- Qualité métier industrielle prouvée
- Classification AI Act définitive
- Résilience multi-région
