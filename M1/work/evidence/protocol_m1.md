# Protocole M1 — DiagOps LoRA

**Date :** 2026-08-03  
**Plateforme :** Mac (MPS/CPU) — runs de référence GPU reportés  
**Modèle :** `Qwen/Qwen3-0.6B` révision `c1899de289a04d12100db370d81485cdf75e47ca`

## Question

La spécialisation LoRA de Qwen3-0.6B améliore-t-elle suffisamment le diagnostic JSON DiagOps (vs baseline brute) pour justifier son intégration derrière `POST /diagnose` ?

## Hypothèse principale

- **Si** on adapte Qwen3-0.6B avec LoRA (r=16, α=32) sur 320 paires annotées,
- **Alors** la conformité schéma, l'exactitude `equipment_id` et le macro-F1 `severity` s'améliorent vs baseline,
- **Parce que** le modèle apprend le format DiagOps et le vocabulaire maintenance du corpus.

## Système contrôle

| Élément | Valeur |
|---|---|
| Modèle / révision | `Qwen/Qwen3-0.6B` @ `c1899de289a04d12100db370d81485cdf75e47ca` |
| Prompt / chat template | starter `src/prompting.py`, `enable_thinking: false` |
| Génération | `max_new_tokens=256`, `do_sample=false`, `temperature=0.0` |
| Split / seed | 320 train / 80 val, seed `42` depuis `diagops_train.jsonl` |
| Métriques | JSON parseable, schéma, equipment_id, macro-F1 severity, review, lexical, latence, mémoire |
| Environnement | voir `work/environment.json` |

## Runs

| Run | Variable modifiée | Valeur | Prédiction avant exécution |
|---|---|---|---|
| Baseline | aucune | sans LoRA | JSON souvent fragile ; severity moins stable |
| Reference LoRA | aucune (config brief) | r=16, α=32, LR 2e-4, 3 epochs | Gain net sur schéma et equipment_id |
| Variation 1 | `lora.r` (+ alpha) | r=8, α=16 | Moins de surapprentissage, généralisation ≥ référence |
| Variation 2 | `learning_rate` | 1e-4 | Moins d'erreurs de format, F1 severity plus stable |
| Smoke Mac | hors protocole | 1 epoch, batch 1 | Preuve de pipeline local uniquement |

## Règle de décision (avant résultats)

- **Retenir un candidat** si, sur validation (puis test après gel), les seuils Brief 2 sont atteints **et** le run est reproductible (idéalement GPU commun).
- **Rejeter** si régression claire vs baseline sur schéma / equipment_id / severity, ou si smoke Mac seul ne permet pas de comparer.
- **Expérience complémentaire** si gain partiel, variance élevée, ou absence de run GPU de référence → **prolonger**.

## Gel

- Candidat gelé : *à renseigner après comparaison validation*
- Config path : *à renseigner*
- Date / auteur : 2026-08-03 — apprenant solo (Mac)

## Notes Mac

Les configs `configs/mac_smoke/` et sorties `work/smoke_mac/` sont **explicitement exclues** des preuves de promotion. Elles valident uniquement l'exécutabilité locale.
