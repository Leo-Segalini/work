# Synthèse des données sensibles (PII) — M2

**Occurrences détectées :** 3

## Règles

| rule_id | Signification | Décision |
|---|---|---|
| PII-EMAIL | adresse électronique | mask_and_keep |
| PII-PHONE | numéro de téléphone | mask_and_keep |
| PII-PERSON | indice de personne (Mme/M./Prénom X.) | mask_and_keep |

## Cas relevés

| row_identifier | rule_id | extrait observé |
|---|---|---|
| MNT-2026S1-1121 | PII-PHONE | `Rappeler Nadia B. au 06 12 34 56 78.` |
| MNT-2026S1-1121 | PII-PERSON | `Rappeler Nadia B. au 06 12 34 56 78.` |
| MNT-2026S1-1334 | PII-EMAIL | `Compte rendu transmis à leo.martin@example.test.` |

## Position

- Les identifiants techniques (`EQ-…`, `EVT-…`, `MNT-…`) ne sont **pas** traités comme PII.
- Les notes masquées sont écrites dans `output/processed/maintenance_history.csv`.
- Les fichiers bruts de `data_pack/` restent inchangés.
