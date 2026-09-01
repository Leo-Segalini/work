# Diagnostic multi-source M3 — DiagOps

**Décision :** `utilisable sous conditions`  
**Point de départ M2 :** `work/M2/output/processed/` (préparation personnelle)

## Réponses aux 12 questions (synthèse)

1. **Ligne capteur** = une mesure à un instant pour un équipement et un capteur. **Clé logique** : `equipment_id + timestamp + sensor_name` (reconstruite, non fournie).
2. **Période observée** : 2025-12-28 → 2026-07-04 UTC ; pas nominal **6 h** (médiane proche, écarts possibles). Voir `series_overview.csv`.
3. **Couverture** : **35** équipements instrumentés / **411** dans le parc préparé (**8,5 %**). SITE-OUEST et types non instrumentés sous-représentés.
4. **Source** : fichier CSV livré dans `data_pack/` ; pas de PII textuelle détectée. Équipements non couverts : pas de capteur → pas de remplacement automatique (absence documentée).
5. **Défauts temporels** : horodatages naïfs (UTC assumé), doublons stricts/conflictuels, sentinelles `-999`, unités incohérentes — quantifiés dans `quarantine.csv`.
6. **Atypiques** : kPa→bar = **normalisation** (577 kPa ≈ 5,77 bar plausible) ; `-999` = **erreur** (exclue) ; doublon conflictuel = **indécidable sans métier** → exclusion.
7. **Règles M2** : toutes **conservées** via reprise des tables `processed/` ; règles capteurs **nouvelles** dans `registre_regles.md`. Non-régression : empreintes SHA256 des 3 tables M2 inchangées à la reprise.
8. **Rapprochement** : fenêtre **−48 h / +24 h** autour de chaque événement ; **2463** couples ; **84** événements avec mesures / **418** sans ; **46433** mesures hors fenêtre.
9. **Agrégats** : grain `equipment_id × sensor_name` (min/max/mean/std) — perd la dynamique intra-journée et les corrélations inter-capteurs.
10. **Flux & cycle de vie** : voir `docs/flux_et_cycle_de_vie.md` ; destinataires : équipe data (rejeu) + métier maintenance (couverture).
11. **Risques** : mesures horodatées + croisement interventions = vigilance présence humaine ; conservation : bruts intacts + `processed/` + quarantaine ; conclusions limitées au parc instrumenté.
12. **Transmission M4** : **sous conditions** — utiliser `output/processed/` + lire `quarantine.csv` ; rejeu : `python -m src.data_pipeline --input … --output …`.

## Arbitrages appliqués (pas d'intégration silencieuse)

| Problème | Décision | Règle |
|---|---|---|
| `pressure_bar` en kPa | conversion 0,01 → bar | SEN-UNIT-001 |
| `TEMPERATURE_C` | alias → `temperature_c` | SEN-NAME-001 |
| Sentinelles `-999` | exclusion | SEN-SENT-001 |
| FK équipement absent (M2) | exclusion | SEN-FK-001 |
| Doublon conflictuel | exclusion | SEN-DUP-002 |
| Hors plage après conversion | exclusion | SEN-RANGE-001 |

## Chiffres clés

| Indicateur | Valeur |
|---|---:|
| Lignes capteurs brutes | 50 401 |
| Conservées dans `processed/` | 48 860 |
| Exclues | 1 531 |
| Séries (équipement × capteur) | 68 |
| Couverture parc | 8,5 % |
