# Model card — DiagOps M1

## Identification

- modèle de base : `Qwen/Qwen3-0.6B`
- révision : `c1899de289a04d12100db370d81485cdf75e47ca`
- adaptateur : *non promu — en attente run GPU de référence*
- commit du dépôt : *à renseigner*
- date : 2026-08-03

## Usage prévu

Transformer un rapport technicien en JSON DiagOps pour assister la maintenance.  
La revue humaine reste obligatoire (`requires_human_review`). Aucune commande d'équipement.

## Données

- origine : `data_pack/2026-S1/annotations/` (synthétique formation)
- volumes : 320 train / 80 validation / 100 test (test non ouvert avant gel)
- limites : corpus synthétique ; ne pas généraliser à un site réel

## Entraînement

- configuration référence : `configs/lora_reference.yaml` (r=16, α=32, LR 2e-4, 3 epochs)
- variations : r=8 (`variation_1`) ; LR 1e-4 (`variation_2`)
- environnement Mac : MPS (`work/environment.json`) — smoke seulement
- durée GPU référence : *à renseigner après run commun*

## Évaluation

| Métrique | Baseline | Candidat | Écart |
|---|---:|---:|---:|
| JSON parseable | *GPU* | *GPU* | |
| Schéma valide | | | |
| Equipment ID | | | |
| Severity macro-F1 | | | |
| Revue humaine | | | |
| Score textuel | | | |
| Latence p95 | | | |

## Robustesse

Brouillon `work/evidence/robustness_cases.jsonl` (20 cas, familles typo/abbr/ordre/…).  
À reconstruire depuis le **test** après gel.

## Décision

- **prolonger**
- preuves : protocole + splits + configs ; absence de métriques GPU
- risques : promotion prématurée sur smoke Mac
- conditions de réexamen : runs GPU complets + seuils Brief 2

## Limites

Ce modèle ne remplace pas la décision d'un technicien et ne commande aucun équipement.
