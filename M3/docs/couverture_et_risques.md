# Couverture et risques — M3

## Couverture instrumentale

- **411** équipements dans le parc préparé M2
- **35** équipements avec au moins une mesure capteur (**8,5 %**)
- **84 / 502** événements rapprochables d'au moins une mesure (fenêtre −48 h / +24 h)

Les conclusions sur les capteurs ne s'appliquent **pas** au parc entier.

## Risques identifiés

| Risque | Mesure proportionnée |
|---|---|
| Données « fausses » (unités, sentinelles, doublons) | Quarantaine + exclusion tracée ; pas de correction silencieuse |
| Couverture partielle | Décision « sous conditions » ; note de périmètre |
| Horodatage ≈ activité humaine | Pas de réidentification ; agrégats au grain équipement/capteur pour les rapports |
| Volume (~50k lignes) | `processed/` + agrégats ; bruts non dupliqués |

## Conservation

- `data_pack/` : lecture seule, jamais modifié
- `output/processed/` : tables préparées rejouables
- `output/quarantine.csv` : trace des rejets et normalisations
- Durée : session S04 / période `2026-S1` (support pédagogique)
