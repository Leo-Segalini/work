# Analyse des erreurs M1

## Synthèse

- nombre de cas examinés : *à compléter dès disponibilité des predictions validation / smoke*
- méthode d'échantillonnage : erreurs de format en priorité, puis equipment_id, severity, review
- limite principale : sans run GPU de référence, l'analyse quantitative reste provisoire

## Matrice

| ID | Système | Type d'erreur | Champ | Gravité | Hypothèse de cause | Action possible |
|---|---|---|---|---|---|---|
| E01 | baseline (attendu) | format | JSON | haute | modèle non spécialisé | LoRA référence |
| E02 | baseline (attendu) | équipement | equipment_id | haute | invente ou omet l'id | renforcer prompt / LoRA |
| E03 | baseline (attendu) | sévérité | severity | moyenne | lissage medium | variation LR |
| E04–E12 | *réservés* | *à classer sur predictions réelles* | | | | |

> Remplir au moins 12 lignes concrètes dès que `predictions.jsonl` smoke ou validation est disponible. Ne pas inventer de métriques.

## Répartition (provisoire)

- erreurs de format : à mesurer
- erreurs d'équipement : à mesurer
- erreurs de sévérité : à mesurer
- erreurs de revue humaine : à mesurer
- erreurs textuelles : à mesurer
- erreurs critiques pour le métier : fausse sévérité basse / revue absente

## Conclusion

Les erreurs qui changent la décision sont surtout : JSON non parseable, mauvais `equipment_id`, sévérité sous-estimée, `requires_human_review` faux négatif.  
Tant que les exports manquent, la décision reste **prolonger l'expérimentation** (run GPU + matrice complète).
