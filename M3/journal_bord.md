# Journal de bord — M3

## Reprise M2

- Point de départ : **`work/M2/output/processed/`** (préparation personnelle, décision *utilisable sous conditions*).
- Référence commune `m2_for_m3` disponible mais non utilisée (écart de volumes documenté).

## Présentiel (14 h)

| Date | Activité | Preuve |
|---|---|---|
| 2026-08-24 | Init M3 + venv Python 3.13 | `work/M3/` |
| 2026-08-24 | Audit capteurs avant intégration | `scripts/audit_sensors.py`, `output/audit/` |
| 2026-08-24 | Pipeline multi-source | `output/processed/`, quarantaine, alignment, décision *sous conditions* |
| 2026-08-24 | Docs flux / couverture / diagnostic | `docs/` |

## Online (6 h)

| Date | Activité | Preuve |
|---|---|---|
| 2026-08-24 | Modèles SQLAlchemy (4 entités) | `src/db/models.py` |
| 2026-08-24 | 2 migrations Alembic upgrade/downgrade | `alembic/versions/` |
| 2026-08-24 | Import idempotent capteurs | `scripts/db_workflow.py`, idempotence OK |
| 2026-08-24 | Requêtes + résultats | `output/db/query_results.json` |

## Brief 2 online — capacité et transmission M4

| Date | Activité | Hypothèse / résultat |
|---|---|---|
| 2026-08-31 | Analyse capacité + segmentation KMeans | 8,5 % couverture ; SITE-OUEST 0/16 |
| 2026-08-31 | Augmentation bruit + décalage temporel | `AUG-NOISE-001`, `AUG-SHIFT-001` |
| 2026-08-31 | Génération SITE-OUEST (marginal + SMOTE) | 204 lignes ; détecteur v1 : 8× R-KEY |
| 2026-08-31 | Détecteur v2 (clip plages) | 8× R-KEY inchangé — cause = clés logiques |
| 2026-08-31 | Détection control_batch | 4978 réelle / 752 fabriquée / 270 indécidable |
| 2026-08-31 | Laplace SITE-OUEST (ε 0,1 / 1 / 10) | compromis utilité/protection documenté |
| 2026-08-31 | Jeu transmission M4 | 48 860 réelles + 200 synthétiques |

**Commande :** `PYTHONPATH=. python scripts/brief2_run.py` ou `launch.py` option 7.

**Interface explorateur :** `streamlit run ui/explorer_app.py` ou `launch.py` option 8.

**Livrables :** `docs/decision_transmission_m4.md`, `output/brief2/verdicts_control_batch.csv`, `docs/registre_regles_brief2.md`.

## Décisions

- **M4 :** `utilisable sous conditions` — couverture capteurs ~8,5 % du parc ; utiliser `processed/` + quarantaine.
- **Stockage :** SQLite relationnel (vs Parquet seul) pour FK, migrations, idempotence.
- **Orphelins capteurs :** FK RESTRICT → rejet compté, pas de mesure sans équipement.
- **Données suspectes :** exclusion tracée (kPa, sentinelles, doublons) — jamais de correction silencieuse.

## Limites ouvertes

- 39 lignes capteurs rejetées en DB (valeurs illisibles résiduelles).
- Notebook `m3_base_de_donnees_atlas.ipynb` : fil conducteur ; code durable dans `src/db/`.
- Brief M2 « aller plus loin » non réalisé (facultatif).
- Brief 2 : 8 doublons de clé logique (`R-KEY`) sur génération SITE-OUEST — non transmis intégralement à M4.
