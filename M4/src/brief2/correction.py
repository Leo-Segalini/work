"""Brief 2 — correction principale : retrieval lexical-first."""

from __future__ import annotations

import time
from pathlib import Path

import yaml

from ..rag_pipeline import answer_question, evaluate_rag
from ..knowledge import load_corpus
from ..io_contracts import load_questions
from ..retrieval import rank_lexical, rank_vector


def rank_lexical_first(
    query: str,
    documents: list[dict],
    embedding_model: str,
    top_k: int = 3,
    min_lexical_score: float = 2.0,
) -> tuple[list[dict], str]:
    """Lexical d'abord ; vectoriel seulement si score lexical insuffisant."""
    lex = rank_lexical(query, documents, top_k=top_k)
    if lex and lex[0].get("score", 0) >= min_lexical_score:
        return lex, "lexical"
    vec = rank_vector(query, documents, embedding_model, top_k=top_k)
    return vec, "vector_fallback"


def evaluate_correction(config_path: Path, output_dir: Path) -> dict:
    """Compare vector seul vs politique lexical-first sur calibration."""
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    root = config_path.resolve().parents[1]
    manifest = (root / cfg["manifest"]).resolve()
    documents = (root / cfg["documents"]).resolve()
    questions_path = (root / cfg["questions"]).resolve()
    embedding = cfg["vector"]["embedding_model"]
    if embedding == "TO_DOCUMENT_BEFORE_RUN":
        embedding = "sentence-transformers/all-MiniLM-L6-v2"
    top_k = int(cfg["lexical"]["top_k"])

    corpus = load_corpus(manifest, documents)
    questions = [q for q in load_questions(questions_path) if q["split"] == "calibration"]

    before = {"strategy": "vector", "recall": 0, "latency_ms": 0, "n": 0}
    after = {"strategy": "lexical_first", "recall": 0, "latency_ms": 0, "n": 0}

    for q in questions:
        role = q["role"]
        from ..knowledge import admissible_documents

        docs = admissible_documents(corpus, role)
        expected = q.get("expected_document_ids") or []

        t0 = time.perf_counter()
        vec_hits = rank_vector(q["question"], docs, embedding, top_k=top_k)
        before["latency_ms"] += (time.perf_counter() - t0) * 1000
        before["n"] += 1
        if expected and any(d in [h["document_id"] for h in vec_hits] for d in expected):
            before["recall"] += 1

        t0 = time.perf_counter()
        lf_hits, _ = rank_lexical_first(q["question"], docs, embedding, top_k=top_k)
        after["latency_ms"] += (time.perf_counter() - t0) * 1000
        after["n"] += 1
        if expected and any(d in [h["document_id"] for h in lf_hits] for d in expected):
            after["recall"] += 1

    for bucket in (before, after):
        bucket["recall_at_k"] = round(bucket["recall"] / max(bucket["n"], 1), 4)
        bucket["avg_latency_ms"] = round(bucket["latency_ms"] / max(bucket["n"], 1), 2)

    correction = {
        "hypothesis": "Latence vectorielle élevée sans gain recall@k vs lexical sur calibration",
        "change": "Politique lexical-first avec repli vectoriel (min_lexical_score=2.0)",
        "before": before,
        "after": after,
        "expected_gain": "Latence divisée ~10x si lexical suffit",
        "possible_regression": "Questions ambiguës nécessitant sémantique pure",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    import json

    (output_dir / "correction_retrieval.json").write_text(
        json.dumps(correction, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return correction
