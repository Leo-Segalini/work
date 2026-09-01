# Évaluation DiagOps M0

Essais réalisés le **2026-08-03** sur `data_pack/2026-S1/reports/reports.jsonl`
via `POST /diagnose` (modèle `Qwen/Qwen2.5-7B-Instruct`, API Hugging Face Inference).

Objectif : intégrer le modèle, observer son comportement et documenter ses limites — pas prouver qu'il est parfait.

## Méthode

1. API démarrée localement (`uvicorn app.main:app --reload --app-dir .`).
2. Appels successifs sur cinq rapports du data pack.
3. Un cas ambigu additionnel pour vérifier la robustesse.

## Résultats (5 rapports du data pack)

| report_id | Symptôme extrait | Sévérité | Hypothèse de panne | Limite observée |
|---|---|---|---|---|
| RPT-2026S1-0001 | Vibration plus forte et bruit métallique au démarrage | medium | Dégradation des roulements ou problème de lubrification | Sévérité prudente (`medium`) malgré température carter 71 °C et bruit métallique ; une lecture métier pourrait viser `high` |
| RPT-2026S1-0002 | Avance irrégulière et arrêts courts | medium | Décalage de la courroie ou problème de tension | Hypothèse cohérente avec la note ; pas d'escalade malgré deux arrêts en moins d'une heure |
| RPT-2026S1-0003 | Pression de sortie instable et purge automatique activée | medium | Fuite d'air vers le raccord aval | Reprend bien l'hypothèse déjà suggérée par le technicien ; faible valeur ajoutée diagnostique |
| RPT-2026S1-0004 | Odeur de chauffe près du moteur et débit faible | medium | Encrassement de la grille d'entrée et surchauffe moteur | Signaux de chauffe + intensité élevée : sévérité encore `medium` (sous-estimation possible) |
| RPT-2026S1-0005 | Débit inférieur à la consigne malgré vanne ouverte | medium | Filtre amont colmaté | Diagnostic aligné sur l'intuition du technicien ; confiance élevée (0.8) sans preuve terrain |

## Cas ambigu (robustesse)

| report_id | Note | Symptôme | Sévérité | Confiance | Revue humaine |
|---|---|---|---|---|---|
| RPT-AMBIGU | « Quelque chose ne va pas sur la machine. » | Problème inconnu | low | 0.3 | `true` (attendu) |

Le modèle baisse correctement la confiance et force la revue humaine lorsque le texte est trop vague.

## Observations transverses

- Les cinq rapports nominaux renvoient un JSON conforme au contrat DiagOps.
- La sévérité se concentre sur `medium` : le modèle lisse les nuances critiques.
- `requires_human_review` reste souvent `false` dès que la confiance dépasse 0.6 — en production, une revue systématique resterait souhaitable.
- `evidence` reprend des fragments du rapport (utile) mais n'est pas une preuve capteur.
- Latence observée : environ 1 à 2 s par appel Inference (variable selon charge HF).
- Sans `HF_TOKEN`, l'API répond `503` ; JSON invalide / panne HF → `502` ; note vide → `422`.

## Changelog

| Date | Changement |
|---|---|
| 2026-08-03 | Gabarit initial |
| 2026-08-03 | Évaluation réelle sur 5 rapports + cas ambigu |
