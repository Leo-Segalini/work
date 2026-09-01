# Rapport d'audit DiagOps M2

**Décision :** `utilisable sous conditions`

Anomalies isolées en quarantaine et/ou PII masquées ; ne pas réutiliser les notes brutes ; contrôler les FK restantes avant M3.

## 1. Fichiers et relations

- `equipment.csv` : inventaire des équipements (clé `equipment_id`).
- `events.csv` : événements liés à un équipement (clé `event_id`, FK `equipment_id`).
- `maintenance_history.csv` : interventions (clé `maintenance_id`, FK `equipment_id` + `event_id`).

| Source | Lignes brutes | SHA-256 |
|---|---:|---|
| equipment | 420 | `d8c51e4cb152…` |
| events | 520 | `4a7d3b517856…` |
| maintenance | 1800 | `635d354bb8ce…` |

## 2. Lisibilité

Les trois CSV sont présents et lisibles depuis `data_pack/2026-S1/`.

## 3. Identifiants, doublons, relations

- Rejets liés aux IDs/FK : 29

## 4. Règles métier non respectées

| rule_id | effectif |
|---|---:|
| MNT-DUP | 10 |
| EQ-DUP | 8 |
| EVT-DUP | 8 |
| MNT-NEG | 2 |
| EQ-NEG | 1 |
| EVT-DATE | 1 |
| EVT-FK-EQ | 1 |
| EVT-SEV | 1 |
| EVT-TYPE | 1 |
| MNT-DATE | 1 |
| MNT-FK-EQ | 1 |
| MNT-FK-EVT | 1 |
| MNT-TYPE | 1 |
| PII-EMAIL | 1 |
| PII-PERSON | 1 |
| PII-PHONE | 1 |

## 5–6. Corrections certaines vs examen métier

- **Corrigé automatiquement :** masquage PII dans les notes (`mask_and_keep`).
- **Mis à l'écart :** doublons, FK cassées, domaines hors schéma, dates/valeurs impossibles (`quarantine`).

## 7. Informations personnelles

Voir `reports/pii_findings.md`. Les notes contenant email/téléphone/personne sont masquées dans la version préparée.

## 8. Couverture (aperçu)

Effectifs `site_id` (top) :
- SITE-NORD: 176
- SITE-SUD: 137
- SITE-EST: 91
- SITE-OUEST: 16

## 9. Erreurs M1 (limites)

La référence `reference_runs/m1_for_m2/` peut être croisée par comptages simples. Pas de causalité affirmée si effectifs faibles.

## 10. Transmission à M3

**Statut :** `utilisable sous conditions`

Conditions : utiliser uniquement `output/processed/` ; consulter `quarantine.csv` ; ne pas réinjecter les notes brutes contenant de la PII.

Lignes en quarantaine (hors masquage seul) : 37
