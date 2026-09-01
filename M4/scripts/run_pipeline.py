#!/usr/bin/env python3
"""Orchestrateur M4 — modèle capteur + RAG + menaces + docs."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.model_eval import evaluate_models  # noqa: E402
from src.rag_pipeline import evaluate_rag  # noqa: E402
from src.threats import THREAT_CASES, run_threat_checks  # noqa: E402

DATA = ROOT / "../../data_pack/2026-S1"


def write_docs(results_dir: Path, model_summary: dict, rag_summary: dict) -> None:
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)

    best = model_summary["selected_model"]
    cand = model_summary["candidates"][best]["calibration_full"]
    base = model_summary["baseline_m3_calibration"]

    (docs / "protocole_evaluation.md").write_text(
        f"""# Protocole d'évaluation M4

- **Date de gel :** 2026-08-31
- **Graine :** 20260831
- **Cible :** provenance capteur (`réelle` / `fabriquée`) — pas prédiction de panne
- **Groupe :** `window_id` (30 mesures/fenêtre, split GroupShuffleSplit 80/20)
- **Calibration :** `sensor_calibration.csv` (900 lignes, 30 fenêtres)
- **Test scellé :** `sensor_test.csv` (1800 lignes) — oracle formateur

## Seuils d'acceptation (calibration)

| Métrique | Baseline M3 | Modèle retenu ({best}) |
|---|---:|---:|
| F1 fabriquée | {base['f1']} | {cand['f1']} |
| Recall | {base['recall']} | {cand['recall']} |
| Precision | {base['precision']} | {cand['precision']} |

## RAG

- Embedding : `{rag_summary['embedding_model']}`
- Stratégies : none, lexical, vector
- Abstention si `answerable=false` ou preuves insuffisantes
""",
        encoding="utf-8",
    )

    (docs / "benchmark_modele.md").write_text(
        f"""# Benchmark modèle capteur

Modèle retenu : **{best}**

```json
{json.dumps(model_summary, ensure_ascii=False, indent=2)}
```
""",
        encoding="utf-8",
    )

    (docs / "benchmark_retrieval.md").write_text(
        f"""# Benchmark retrieval

```json
{json.dumps(rag_summary, ensure_ascii=False, indent=2)}
```
""",
        encoding="utf-8",
    )

    threat_checks = run_threat_checks()
    (docs / "threat_model.md").write_text(
        """# Threat model M4

| ID | Attaque | Détection | Atténuation | Risque résiduel |
|---|---|---|---|---|
"""
        + "\n".join(
            f"| {c['id']} | {c['attack']} | {c['detection']} | {c['mitigation']} | {c['residual']} |"
            for c in THREAT_CASES
        )
        + "\n\n## Vérifications automatiques\n\n```json\n"
        + json.dumps(threat_checks, ensure_ascii=False, indent=2)
        + "\n```\n",
        encoding="utf-8",
    )

    decision = "evaluer davantage"
    if cand["f1"] > base["f1"] and cand["recall"] > base["recall"]:
        decision = "adopter sous conditions (test scellé formateur requis)"
    elif cand["f1"] <= base["f1"]:
        decision = "maintenir baseline M3"

    (docs / "matrice_decision.md").write_text(
        f"""# Matrice de décision M4

| Dimension | Baseline M3 | Modèle {best} | RAG vectoriel |
|---|---|---|---|
| Qualité (F1 cal.) | {base['f1']} | {cand['f1']} | recall@k {rag_summary['strategies'].get('vector', {}).get('recall_at_k', '—')} |
| Robustesse | règles figées | features + règles | citations vérifiables |
| Latence | {model_summary['baseline_m3_validation'].get('latency_ms_per_row', '—')} ms/ligne | {model_summary['candidates'][best]['validation'].get('latency_ms_per_row', '—')} ms/ligne | {rag_summary['strategies'].get('vector', {}).get('avg_latency_ms', '—')} ms/q |
| Réversibilité | haute | haute | haute |

## Décision

**{decision}**

Conditions :
- validation formateur sur test scellé ;
- provenance synthétique M3 documentée — pas de conclusion parc entier ;
- agent limité à une action, sans effet externe.
""",
        encoding="utf-8",
    )

    (docs / "model_card.md").write_text(
        f"""# Model card — M4

## Modèle capteur ({best})

- **Cible :** détection provenance fabriquée vs réelle
- **Features :** règles M3 binaires + valeur + capteur one-hot
- **Calibration F1 :** {cand['f1']}
- **Limites :** ne prédit pas une panne ; données synthétiques formation

## RAG

- **Modèle embeddings :** {rag_summary['embedding_model']}
- **Corpus :** {rag_summary['corpus_documents']} documents versionnés
- **Contrat :** citation obligatoire, abstention sans preuve
""",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Pipeline M4 complet")
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    parser.add_argument("--skip-rag", action="store_true", help="Skip vector retrieval (slow)")
    args = parser.parse_args()

    model_summary = evaluate_models(
        (DATA / "model_eval/sensor_calibration.csv").resolve(),
        (DATA / "model_eval/sensor_test.csv").resolve(),
        args.output,
        ROOT / "configs/model.yaml",
    )

    if args.skip_rag:
        rag_summary = {"embedding_model": "skipped", "strategies": {}, "corpus_documents": 0}
    else:
        cfg_path = ROOT / "configs/retrieval.yaml"
        cfg = cfg_path.read_text(encoding="utf-8").replace(
            "TO_DOCUMENT_BEFORE_RUN", "sentence-transformers/all-MiniLM-L6-v2"
        )
        tmp = ROOT / "configs/retrieval.resolved.yaml"
        tmp.write_text(cfg, encoding="utf-8")
        rag_summary = evaluate_rag(tmp, args.output)

    write_docs(args.output, model_summary, rag_summary)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": model_summary,
        "rag": rag_summary,
        "output": str(args.output.resolve()),
    }
    (args.output / "m4_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(
        {
            "selected_model": model_summary["selected_model"],
            "baseline_f1": model_summary["baseline_m3_calibration"]["f1"],
            "model_f1": model_summary["candidates"][model_summary["selected_model"]]["calibration_full"]["f1"],
            "rag_vector_recall": rag_summary.get("strategies", {}).get("vector", {}).get("recall_at_k"),
            "output": str(args.output.resolve()),
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
