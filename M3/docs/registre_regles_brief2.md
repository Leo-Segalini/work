# Registre de règles — Brief 2 (détection fabrication)

Complète le registre brief 1. Statuts : **actif**, **calibré**, **inopérant**.

| ID | Portée | Description | Statut | Justification brief 2 |
|---|---|---|---|---|
| D-SCHEMA | ligne | `sensor_name` hors liste M3 | actif | attrape fabrications grossières |
| D-FORMAT | ligne | timestamp hors pas 6 h ou période | calibré | seul → `indécidable` (control_sample) |
| D-RANGE | ligne | valeur hors plage ou sentinelle | actif | 212 lignes control_batch |
| D-UNIT | ligne | unité incohérente avec capteur | actif | 180 lignes (ex. kPa sur pressure_bar) |
| D-FK | ligne | `equipment_id` absent du parc | actif | 210 lignes |
| D-PRECISION | ligne | > 3 décimales | actif | 150 lignes |
| D-MS-EVT | multi-source | mesure calme pendant événement critical/high | actif | détection greffe events.csv |
| D-OK | ligne | aucune règle déclenchée | actif | 4 978 lignes réelles |

**Règles brief 1 réévaluées :**

- Règles de format seules : trop permissives pour trancher → `indécidable`.
- Règles M2/M3 de schéma : toujours pertinentes sur fabrications grossières.
- Rapprochement temporel brief 1 : réutilisé comme instrument de détection (`D-MS-EVT`).
