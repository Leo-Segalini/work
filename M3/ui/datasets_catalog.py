"""Catalogue des jeux de données DiagOps M3 — descriptions pour l'explorateur."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DatasetInfo:
    id: str
    title: str
    path: str
    phase: str
    description: str
    columns: str = ""
    usage: str = ""


def catalog(root: Path, data_pack: Path) -> list[DatasetInfo]:
    """Liste documentée des jeux de données connus."""
    return [
        DatasetInfo(
            id="raw_equipment",
            title="Équipements (brut)",
            path=str(data_pack / "equipment/equipment.csv"),
            phase="data_pack",
            description="Référentiel parc usine — 420 équipements, 4 sites.",
            columns="equipment_id, site_id, equipment_type, criticality, rated_power_kw…",
            usage="Source M2/M3, jamais modifiée.",
        ),
        DatasetInfo(
            id="raw_events",
            title="Événements (brut)",
            path=str(data_pack / "events/events.csv"),
            phase="data_pack",
            description="Incidents et alertes supervision — 520 lignes brutes.",
            columns="event_id, equipment_id, severity, start_at, end_at…",
            usage="Rapprochement temporel avec capteurs.",
        ),
        DatasetInfo(
            id="raw_sensors",
            title="Capteurs (brut)",
            path=str(data_pack / "sensors/sensor_readings.csv"),
            phase="data_pack",
            description="Mesures supervision export batch — ~50 401 lignes.",
            columns="equipment_id, timestamp, sensor_name, value, unit, period",
            usage="Entrée pipeline brief 1.",
        ),
        DatasetInfo(
            id="control_batch",
            title="Lot de contrôle (brief 2)",
            path=str(data_pack / "sensors_control/control_batch.csv"),
            phase="data_pack",
            description="~6 000 mesures dont une partie fabriquée, sans colonne provenance.",
            columns="equipment_id, timestamp, sensor_name, value, unit, period",
            usage="Calibration détection fabrication.",
        ),
        DatasetInfo(
            id="processed_equipment",
            title="Équipements (préparé M2→M3)",
            path=str(root / "output/processed/equipment.csv"),
            phase="brief1",
            description="411 équipements après quarantaine M2 — base du parc exploitable.",
            columns="equipment_id, site_id, equipment_type, criticality…",
            usage="FK capteurs, couverture, segmentation.",
        ),
        DatasetInfo(
            id="processed_sensors",
            title="Capteurs (préparé)",
            path=str(root / "output/processed/sensor_readings.csv"),
            phase="brief1",
            description="48 860 mesures conservées (kPa→bar, sentinelles exclues, FK validées).",
            columns="equipment_id, timestamp, sensor_name, value, unit, period",
            usage="Agrégats, alignment, DB, brief 2.",
        ),
        DatasetInfo(
            id="quarantine",
            title="Quarantaine",
            path=str(root / "output/quarantine.csv"),
            phase="brief1",
            description="Lignes rejetées avec règle et raison (M2 + capteurs).",
            columns="source, rule_id, reason, row_data…",
            usage="Traçabilité des exclusions.",
        ),
        DatasetInfo(
            id="alignment",
            title="Rapprochement mesures ↔ événements",
            path=str(root / "output/alignment/measures_events.csv"),
            phase="brief1",
            description="2 463 couples mesure-événement (fenêtre −48h/+24h).",
            columns="measure_id, event_id, equipment_id, delta_hours…",
            usage="Analyse multi-source, détection D-MS-EVT.",
        ),
        DatasetInfo(
            id="validation",
            title="Rapport de validation",
            path=str(root / "output/validation_report.json"),
            phase="brief1",
            description="Synthèse pipeline : volumes, couverture 8,5 %, alignment, règles.",
            columns="JSON structuré",
            usage="Décision transmission brief 1.",
        ),
        DatasetInfo(
            id="db_queries",
            title="Résultats requêtes DB",
            path=str(root / "output/db/query_results.json"),
            phase="brief1_online",
            description="Top mesures, comptages tables SQLite après import idempotent.",
            columns="JSON structuré",
            usage="Preuve brief online.",
        ),
        DatasetInfo(
            id="brief2_summary",
            title="Synthèse brief 2",
            path=str(root / "output/brief2/brief2_summary.json"),
            phase="brief2",
            description="Capacité, génération SITE-OUEST, verdicts, Laplace, décision M4.",
            columns="JSON structuré",
            usage="Vue consolidée brief 2.",
        ),
        DatasetInfo(
            id="verdicts",
            title="Verdicts control_batch",
            path=str(root / "output/brief2/verdicts_control_batch.csv"),
            phase="brief2",
            description="Un verdict par ligne : réelle / fabriquée / indécidable + règle.",
            columns="row_identifier, verdict, rule_id, all_rules",
            usage="Livrable détection brief 2.",
        ),
        DatasetInfo(
            id="transmission_m4",
            title="Jeu transmis à M4",
            path=str(root / "output/brief2/transmission_m4/sensor_readings_m4.csv"),
            phase="brief2",
            description="48 860 réelles + 200 synthétiques SITE-OUEST avec provenance.",
            columns="… + provenance, procedure_id",
            usage="Entrée module 4 sous conditions.",
        ),
        DatasetInfo(
            id="generated_site",
            title="Génération SITE-OUEST",
            path=str(root / "output/brief2/generated_site_ouest.csv"),
            phase="brief2",
            description="204 lignes synthétiques (marginal + SMOTE) pour site non instrumenté.",
            columns="equipment_id, timestamp, sensor_name, value, provenance, procedure_id",
            usage="Comparaison réel/fabriqué.",
        ),
    ]


PHASE_LABELS = {
    "data_pack": "📦 Data pack (lecture seule)",
    "brief1": "🔧 Brief 1 — pipeline multi-source",
    "brief1_online": "🗄️ Brief 1 online — base de données",
    "brief2": "🧪 Brief 2 — capacité & transmission M4",
}
