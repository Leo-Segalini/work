# Journal de bord — M2

## Reprise M0–M1

- Référence commune M1 consultée : `data_pack/2026-S1/reference_runs/m1_for_m2/` (comptages / limites, pas de causalité forcée).
- Comparaison éventuelle avec ma production M1 : smoke LoRA Mac (schéma ~98 %, composite ~90) ≠ run GPU de référence ; M1 « référence » encore partiel (pas de `--allow-test` local prolongé).
- Décisions structurantes : bruts `data_pack/` en lecture seule ; pipeline hybride + notebooks ; PII = regex email/tél. + heuristique personne ; décision M3 = `utilisable sous conditions`.
- Preuves conservées : `output/validation_report.json`, `output/quarantine.csv`, `reports/audit_report.md`, `reports/pii_findings.md`, notebook stats exécuté + HTML.
- Limites encore ouvertes : FK/doublons en quarantaine à arbitrer métier ; SITE-OUEST sous-représenté ; notes brutes hors `processed/` interdites.

## Hypothèses formulées avant analyse

| Date | Hypothèse | Mesure prévue | Résultat | Décision |
|---|---|---|---|---|
| 2026-08-03 | Les 3 CSV sont jointables sans explosion de cardinalité | Left joins + indicateur `_merge` | Cardinalité stable mais orphelins FK + inflation légère liée aux doublons d'ID | Quarantaine des doublons / FK ; ne pas « forcer » le merge |
| 2026-08-03 | Des notes de maintenance contiennent de la PII | Scan regex email/tél./personne | 3 hits (2 tickets) | `mask_and_keep` + journal PII |
| 2026-08-03 | La distribution des arrêts est asymétrique | mean vs median + histogramme | Moyenne > médiane, queue longue | Préférer médiane / quantiles pour le pilotage |
| 2026-08-03 | SITE-OUEST est trop petit pour des conclusions fermes | Effectifs par site | 16 équipements seulement | Signaler la fragilité ; pas de comparaison agressive |

## Activités et preuves produites

| Date | Activité | Artefact ou commit | Revue reçue |
|---|---|---|---|
| 2026-08-03 | Init M2 + venv + tests | `work/M2/`, 7 tests verts | — |
| 2026-08-03 | Pipeline validation + PII | `output/processed/`, `quarantine.csv`, `validation_report.json` | — |
| 2026-08-03 | Rapports audit / PII | `reports/audit_report.md`, `reports/pii_findings.md` | — |
| 2026-08-03 | Notebook audit (section 5) | `notebooks/notebook_audit_m2.ipynb` | Option 5 explorée |
| 2026-08-03 | Notebook stats Atlas + figures + HTML | `notebooks/m2_statistiques_atlas.ipynb`, `reports/figures/`, `reports/m2_statistiques_atlas.html` | Option 6 amorcée puis complétée |
| 2026-08-31 | Qualification livraison candidate (aller plus loin) | `src/candidate_qualification.py`, `scripts/qualify_candidate.py`, `aller_plus_loin/`, workflow CI | Décision **REJECTED** (16 blocages) |

## Complément « aller plus loin » (2026-08-31)

| Élément | Détail |
|---|---|
| Lot qualifié | `data_pack/2026-S1/m2_candidate_release/` (r2) |
| Décision | **REJECTED** — ne pas fusionner |
| Bloquants | 16 (6 doublons, 2 collisions historique, 3 domaines, 5 FK) |
| Évolution OK | Colonne `source_system` sur maintenance (`info`) |
| Preuves | `output/candidate_qualification/`, `aller_plus_loin/run_manifest.json` |
| CI | `.github/workflows/m2-qualification.yml` — job socle vert, job candidate rouge attendu |

Hypothèse testée : les contrôles M2 + règles `CAND-*` suffisent à rejeter automatiquement un lot défectueux sans toucher au socle publié. Confirmé.

## Décisions

### Décision

- Options considérées : `utilisable` / `utilisable sous conditions` / `non utilisable en l'état`.
- Preuve déterminante : 37 lignes en quarantaine (doublons, FK, domaines, négatifs) + 3 PII masquées ; tables préparées majoritairement retenues (411/502/1738).
- Choix retenu : **`utilisable sous conditions`**.
- Limites et réversibilité : conditions = consommer uniquement `output/processed/` ; lire `quarantine.csv` ; ne pas réinjecter les notes brutes ; arbitrage métier possible sur chaque `rule_id` sans retoucher `data_pack/`.

## Bilan M2

- Ce que je sais démontrer : audit reproductible (`python3 launch.py` → option 1), détection PII, décision argumentée, stats descriptives avec figures et réponses 1→16, export HTML.
- Ce qui reste incertain : causes métier des doublons / valeurs impossibles ; lien éventuel avec erreurs M1 (effectifs faibles).
- Ce que M3 doit reprendre : `output/processed/*.csv` + `quarantine.csv` + ce journal ; ignorer les notes non masquées ; traiter la sous-représentation SITE-OUEST.
