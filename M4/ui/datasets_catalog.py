"""Catalogue des jeux de données DiagOps M4."""

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
    return [
        DatasetInfo(
            id="sensor_calibration",
            title="Capteurs — calibration modèle",
            path=str(data_pack / "model_eval/sensor_calibration.csv"),
            phase="data_pack",
            description="900 lignes, 30 fenêtres — provenance visible (réelle / fabriquée).",
            columns="window_id, equipment_id, timestamp, sensor_name, value, unit, period, provenance",
            usage="Entraînement et validation interne (split par window_id).",
        ),
        DatasetInfo(
            id="sensor_test",
            title="Capteurs — test scellé",
            path=str(data_pack / "model_eval/sensor_test.csv"),
            phase="data_pack",
            description="1 800 lignes, 60 fenêtres — sans étiquette (oracle formateur).",
            columns="window_id, equipment_id, timestamp, sensor_name, value, unit, period",
            usage="Prédictions exportées après gel du candidat.",
        ),
        DatasetInfo(
            id="knowledge_manifest",
            title="Manifeste corpus documentaire",
            path=str(data_pack / "knowledge/manifest.csv"),
            phase="data_pack",
            description="8 documents versionnés : revision, checksum, rôles, sensibilité.",
            columns="document_id, title, revision, status, allowed_roles, checksum_sha256…",
            usage="Admission documents pour RAG.",
        ),
        DatasetInfo(
            id="rag_questions",
            title="Questions RAG gelées",
            path=str(data_pack / "rag_eval/questions.jsonl"),
            phase="data_pack",
            description="Questions calibration + test ; answerable ; expected_document_ids.",
            columns="eval_id, question, role, answerable, expected_document_ids, split",
            usage="Évaluation retrieval et abstention.",
        ),
        DatasetInfo(
            id="m3_baseline",
            title="Baseline M3 (référence)",
            path=str(data_pack / "reference_runs/m3_for_m4/baseline_rules.py"),
            phase="reference",
            description="Règles figées M3-PERIOD, M3-UNIT, M3-RANGE…",
            columns="—",
            usage="Plancher à battre par le modèle ML.",
        ),
        DatasetInfo(
            id="benchmark_modele",
            title="Benchmark modèle",
            path=str(root / "results/benchmark_modele.json"),
            phase="results",
            description="Métriques LR, RF, baseline M3 ; modèle retenu.",
            columns="JSON",
            usage="Décision modèle capteur.",
        ),
        DatasetInfo(
            id="benchmark_retrieval",
            title="Benchmark retrieval",
            path=str(root / "results/benchmark_retrieval.json"),
            phase="results",
            description="Recall@k, abstention, latence par stratégie.",
            columns="JSON",
            usage="Décision RAG.",
        ),
        DatasetInfo(
            id="sensor_predictions",
            title="Prédictions test capteurs",
            path=str(root / "results/sensor_test_predictions.csv"),
            phase="results",
            description="1 800 lignes prédites (provenance estimée + score).",
            columns="… + prediction, score_fabricated, model",
            usage="Soumission formateur (sans oracle local).",
        ),
        DatasetInfo(
            id="rag_results",
            title="Résultats RAG calibration",
            path=str(root / "results/rag_calibration_results.jsonl"),
            phase="results",
            description="Une ligne par question × stratégie : citations, agent, recall.",
            columns="eval_id, strategy, abstained, citations, agent_action…",
            usage="Audit réponses citées.",
        ),
        DatasetInfo(
            id="m4_summary",
            title="Synthèse M4",
            path=str(root / "results/m4_summary.json"),
            phase="results",
            description="Vue consolidée modèle + RAG.",
            columns="JSON",
            usage="Point d'entrée rapide.",
        ),
        DatasetInfo(
            id="matrice_decision",
            title="Matrice de décision",
            path=str(root / "docs/matrice_decision.md"),
            phase="docs",
            description="Comparaison qualité, latence, réversibilité ; décision finale.",
            columns="Markdown",
            usage="Livrable brief 1.",
        ),
    ]


PHASE_LABELS = {
    "data_pack": "📦 Data pack (lecture seule)",
    "reference": "📋 Référence formateur",
    "results": "📊 Résultats M4 (rejouables)",
    "docs": "📝 Documentation livrables",
}
