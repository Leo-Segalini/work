# Décision M1 — état intermédiaire / final provisoire

**Date :** 2026-08-03  
**Plateforme :** Mac (MPS/CPU)  
**Statut :** **Prolonger l'expérimentation**

## Décision

| Option | Retenue |
|---|---|
| Promouvoir | non |
| Ne pas promouvoir | non (trop tôt pour conclure à une régression) |
| **Prolonger** | **oui** |

## Preuves principales

1. Protocole et hypothèses figés avant comparaison (`protocol_m1.md`).
2. Split officiel 320/80 seed 42 produit et versionnable.
3. Configs référence + 2 variations (r=8 ; LR 1e-4) renseignées.
4. Smoke Mac isolé — non utilisé pour promotion.
5. Auto-revue : objection « smoke ≠ référence » acceptée et corrigée.

## Prochaine étape (explicite)

1. Exécuter sur **GPU commun** : baseline validation + LoRA référence + 2 variations.
2. Exporter `metrics_m1.csv` / predictions ; compléter ≥12 erreurs.
3. Geler le candidat ; ouvrir le test (`--allow-test`) une seule fois.
4. Robustesse 20 cas + intégration API ; revoir les seuils Brief 2.

## Risques

- Extrapolater des métriques Mac.
- Ouvrir le test trop tôt.
- Confondre `hf_api` (M0) avec le candidat local Qwen3-0.6B.
