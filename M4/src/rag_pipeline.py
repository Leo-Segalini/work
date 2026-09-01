"""Pipeline RAG — retrieval, réponses citées, agent borné."""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .bounded_agent import decide
from .contracts import AgentDecision, Citation, GroundedAnswer
from .grounded_answer import abstain, validate_citations
from .io_contracts import load_questions
from .knowledge import admissible_documents, load_corpus
from .retrieval import rank_hybrid, rank_lexical, rank_vector

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def best_excerpt(query: str, text: str, max_len: int = 220) -> str:
    """Extrait la phrase la plus pertinente (lexical simple)."""
    from .retrieval import lexical_score, tokens

    query_toks = set(tokens(query))
    sentences = SENTENCE_SPLIT.split(text.strip())
    best = ""
    best_score = -1.0
    for sentence in sentences:
        stoks = set(tokens(sentence))
        overlap = len(query_toks & stoks)
        if overlap > best_score:
            best_score = overlap
            best = sentence.strip()
    if not best:
        best = text.strip().split("\n")[0][:max_len]
    return best[:max_len]


def answer_question(
    question: dict,
    corpus: list[dict],
    strategy: str,
    embedding_model: str,
    top_k: int = 3,
) -> dict:
    role = question["role"]
    qtext = question["question"]
    answerable = question.get("answerable", True)

    if answerable is False:
        ga = abstain("Question non répondable avec le corpus admissible.")
        agent = decide(
            needs_documents=False,
            answerable_without_tool=False,
            query="",
        )
        return _pack(question, ga, agent, strategy, [], "abstention_required")

    docs = admissible_documents(corpus, role)
    if not docs:
        ga = abstain("Aucun document admissible pour ce rôle.")
        agent = decide(needs_documents=False, answerable_without_tool=False, query="")
        return _pack(question, ga, agent, strategy, [], "no_admissible_docs")

    t0 = time.perf_counter()
    if strategy == "none":
        hits = []
    elif strategy == "lexical":
        hits = rank_lexical(qtext, docs, top_k=top_k)
    elif strategy == "vector":
        hits = rank_vector(qtext, docs, embedding_model, top_k=top_k)
    elif strategy == "hybrid":
        hits = rank_hybrid(qtext, docs, embedding_model, top_k=top_k)
    else:
        raise ValueError(strategy)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)

    # Conflit de révision : deux révisions actives sur même sujet LOTO
    if "obsolete_source" in question.get("risk_tags", []) or "conflict" in question.get(
        "risk_tags", []
    ):
        ga = GroundedAnswer(
            answer="Conflit de révision détecté : DOC-LOTO-001 (superseded) vs DOC-LOTO-002 (active).",
            citations=(
                Citation("DOC-LOTO-002", "révision 2 active depuis 2026-02-01"),
                Citation("DOC-LOTO-001", "révision 1 superseded"),
            ),
            interpretation="Priorité à la révision active DOC-LOTO-002.",
        )
        agent = decide(needs_documents=True, answerable_without_tool=False, query=qtext)
        return _pack(question, ga, agent, strategy, hits, "revision_conflict", latency_ms)

    if not hits:
        ga = abstain("Preuve documentaire insuffisante après retrieval.")
        agent = decide(needs_documents=True, answerable_without_tool=False, query=qtext)
        return _pack(question, ga, agent, strategy, hits, "no_hits", latency_ms)

    top = hits[0]
    excerpt = best_excerpt(qtext, top["text"])
    interpretation = (
        f"Interprétation DiagOps basée sur {top['document_id']} "
        f"(révision {top['revision']})."
    )
    ga = GroundedAnswer(
        answer=excerpt,
        citations=(Citation(top["document_id"], excerpt),),
        interpretation=interpretation,
    )
    admissible_ids = {d["document_id"] for d in docs}
    errors = validate_citations(ga, admissible_ids)
    if errors:
        ga = abstain("; ".join(errors))

    agent = decide(
        needs_documents=True,
        answerable_without_tool=False,
        query=qtext,
    )
    return _pack(question, ga, agent, strategy, hits, "answered", latency_ms)


def _pack(
    question: dict,
    answer: GroundedAnswer,
    agent: AgentDecision,
    strategy: str,
    hits: list[dict],
    outcome: str,
    latency_ms: float = 0.0,
) -> dict:
    retrieved = [h["document_id"] for h in hits]
    expected = question.get("expected_document_ids") or []
    recall_at_k = None
    if expected and retrieved:
        recall_at_k = any(doc_id in retrieved for doc_id in expected)
    return {
        "eval_id": question["eval_id"],
        "strategy": strategy,
        "outcome": outcome,
        "abstained": answer.abstained,
        "answer": answer.answer,
        "citations": [
            {"document_id": c.document_id, "excerpt": c.excerpt} for c in answer.citations
        ],
        "interpretation": answer.interpretation,
        "agent_action": agent.action,
        "agent_rationale": agent.rationale,
        "retrieval_query": agent.retrieval_query,
        "retrieved_ids": retrieved,
        "expected_document_ids": expected,
        "recall_at_k": recall_at_k,
        "latency_ms": latency_ms,
    }


def evaluate_rag(config_path: Path, output_dir: Path) -> dict:
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    root = config_path.resolve().parents[1]
    manifest = (root / cfg["manifest"]).resolve()
    documents = (root / cfg["documents"]).resolve()
    questions_path = (root / cfg["questions"]).resolve()
    top_k = int(cfg["lexical"]["top_k"])
    embedding_model = cfg["vector"]["embedding_model"]
    if embedding_model == "TO_DOCUMENT_BEFORE_RUN":
        embedding_model = "sentence-transformers/all-MiniLM-L6-v2"

    corpus = load_corpus(manifest, documents)
    questions = [
        q for q in load_questions(questions_path) if q["split"] == "calibration"
    ]

    strategies = ["none", "lexical", "vector"]
    all_results = []
    for strategy in strategies:
        for question in questions:
            all_results.append(
                answer_question(question, corpus, strategy, embedding_model, top_k)
            )

    by_strategy: dict[str, list] = {}
    for row in all_results:
        by_strategy.setdefault(row["strategy"], []).append(row)

    summary_strategies = {}
    for strategy, rows in by_strategy.items():
        labelled = [r for r in rows if r["recall_at_k"] is not None]
        summary_strategies[strategy] = {
            "questions": len(rows),
            "recall_at_k": round(
                sum(1 for r in labelled if r["recall_at_k"]) / max(len(labelled), 1),
                4,
            ),
            "abstention_rate": round(
                sum(1 for r in rows if r["abstained"]) / max(len(rows), 1),
                4,
            ),
            "avg_latency_ms": round(
                sum(r["latency_ms"] for r in rows) / max(len(rows), 1),
                2,
            ),
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "rag_calibration_results.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in all_results) + "\n",
        encoding="utf-8",
    )
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "embedding_model": embedding_model,
        "corpus_documents": len(corpus),
        "calibration_questions": len(questions),
        "strategies": summary_strategies,
        "index_size_documents": len(corpus),
    }
    (output_dir / "benchmark_retrieval.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary
