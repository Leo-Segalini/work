# Flux de traitement et cycle de vie — M3

## Flux (source → sortie)

```text
data_pack/2026-S1/
├── equipment/events/maintenance (bruts M2)
├── sensors/sensor_readings.csv (brut M3)
└── reference_runs/m2_for_m3/ (référence optionnelle)

        │
        ▼
[1] Reprise tables M2 préparées (personnel ou référence)
        → output/processed/{equipment,events,maintenance}.csv

        ▼
[2] Préparation capteurs (prepare_sensors)
        → normalisations tracées (kPa, alias)
        → exclusions (sentinelles, FK, doublons conflictuels)
        → output/processed/sensor_readings.csv
        → lignes rejetées → quarantine.csv

        ▼
[3] Agrégats + rapprochement événements
        → output/aggregates/by_equipment_sensor.csv
        → output/alignment/measures_events.csv

        ▼
[4] Rapports
        → validation_report.json, registre_regles.md, diagnostic

        ▼
[5] Brief 2 — capacité, augmentation, génération, détection
        → output/brief2/ (verdicts, transmission M4, journal détecteur)
        → docs/decision_transmission_m4.md
```

**Commande de rejeu (brief 1) :**

```bash
cd work/M3 && source .venv/bin/activate
PYTHONPATH=. python -m src.data_pipeline \
  --input ../../data_pack/2026-S1 \
  --output ./output \
  --m2-processed ../M2/output/processed
```

**Commande brief 2 :**

```bash
cd work/M3 && source .venv/bin/activate
PYTHONPATH=. python scripts/brief2_run.py
```

## Cycle de vie

| Étape | Qui | Fréquence | Format |
|---|---|---|---|
| Production capteurs | supervision usine | export batch (6 h nominal) | CSV |
| Livraison | formateur / data pack | statique S04 | `sensor_readings.csv` |
| Préparation | pipeline M3 | à chaque rejeu | `processed/` + quarantaine |
| Fabrication (brief 2) | pipeline brief2 | à la demande, graine fixe | `synthétique` / `augmentée` + `procedure_id` |
| Exploitation M4 | modèle / analytics | consommation | `transmission_m4/sensor_readings_m4.csv` |

**Données fabriquées :** chaque ligne porte `provenance`, `procedure_id`, date de génération (métadonnées `brief2_summary.json`). Validité : période `2026-S1`, périmètre SITE-OUEST pour le synthétique transmis.

**Fin d'utilisabilité :** nouvelle période (`2026-S2`) ou rupture de schéma non documentée.

**Destinataires :** développeur data (rejeu CLI), responsable maintenance (couverture/risques), conformité (quarantaine PII — N/A capteurs numériques).
