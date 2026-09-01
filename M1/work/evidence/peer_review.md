# Revue et reproduction M1 (mode solo / auto-contradictoire)

## Identification

- auteur du run : apprenant solo (Mac)
- relecteur : même apprenant (auto-revue méthodologique — pas de binôme)
- configuration : `configs/lora_reference.yaml` + `configs/mac_smoke/*`
- commit : *à renseigner*

## Reproduction

| Mesure | Original | Reproduction | Écart |
|---|---:|---:|---:|
| Split 320/80 seed 42 | attendu | produit via `src.dataset` | 0 si manifest stable |
| Smoke Mac LoRA | n/a (premier run) | `work/smoke_mac/` | n/a |
| Run GPU référence | non exécuté | — | preuve manquante |

## Contrôle

- versions identifiées : oui (`work/environment.json`)
- seed identifiée : 42
- prompt identique : oui (starter figé)
- split identique : oui (`split_manifest.json`)
- métriques recalculables : oui (scripts starter)

## Objection

- affirmation contestée : « Les métriques smoke Mac peuvent servir à choisir le candidat. »
- preuve recherchée : le brief exige un environnement GPU commun et des configs de référence intactes.
- résultat : objection **validée** — smoke ≠ run de référence.
- impact possible sur la décision : empêche toute promotion basée uniquement sur Mac.

## Correction

- changement effectué : séparation explicite `configs/mac_smoke/` + `work/smoke_mac/` + mention dans `protocol_m1.md`.
- preuve avant : risque de confondre un train 1 epoch batch 1 avec la référence 3 epochs.
- preuve après : protocole et configs smoke étiquetés `smoke: true`.

## Conclusion individuelle

Le pipeline local est reproductible pour l'outillage (splits, env, configs).  
La recommandation expérimentale GPU n'est **pas encore défendable** sans run de référence commun → décision orientée **prolonger**.
