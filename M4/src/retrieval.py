"""Baseline lexicale transparente et contrat d'admission documentaire."""

from __future__ import annotations

import re
import time
from collections import Counter

import numpy as np

TOKEN = re.compile(r"[\wÀ-ÿ-]+", re.UNICODE)


def tokens(text: str) -> list[str]:
    return [token.lower() for token in TOKEN.findall(text)]


def lexical_score(query: str, text: str) -> float:
    query_counts = Counter(tokens(query))
    text_counts = Counter(tokens(text))
    return float(sum(min(count, text_counts[token]) for token, count in query_counts.items()))


def rank_lexical(query: str, documents: list[dict], top_k: int = 3) -> list[dict]:
    ranked = sorted(
        documents,
        key=lambda document: (
            lexical_score(query, document["text"]),
            document["document_id"],
        ),
        reverse=True,
    )
    return [
        {**item, "score": lexical_score(query, item["text"])}
        for item in ranked
        if lexical_score(query, item["text"]) > 0
    ][:top_k]


def rank_vector(
    query: str,
    documents: list[dict],
    model_name: str,
    top_k: int = 3,
) -> list[dict]:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    texts = [doc["text"] for doc in documents]
    t0 = time.perf_counter()
    doc_emb = model.encode(texts, normalize_embeddings=True)
    query_emb = model.encode([query], normalize_embeddings=True)[0]
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    scores = doc_emb @ query_emb
    order = np.argsort(scores)[::-1][:top_k]
    return [
        {**documents[i], "score": float(scores[i]), "latency_ms": latency_ms}
        for i in order
        if scores[i] > 0.05
    ]


def rank_hybrid(
    query: str,
    documents: list[dict],
    model_name: str,
    top_k: int = 3,
) -> list[dict]:
    lex = {d["document_id"]: lexical_score(query, d["text"]) for d in documents}
    vec_hits = rank_vector(query, documents, model_name, top_k=len(documents))
    vec = {h["document_id"]: h["score"] for h in vec_hits}
    combined = []
    for doc in documents:
        did = doc["document_id"]
        score = 0.5 * lex.get(did, 0) + 0.5 * vec.get(did, 0)
        if score > 0:
            combined.append({**doc, "score": score})
    combined.sort(key=lambda d: (-d["score"], d["document_id"]))
    return combined[:top_k]


def admissible(metadata: dict[str, str], role: str) -> bool:
    roles = {item for item in metadata["allowed_roles"].split(";") if item}
    return metadata["status"] == "active" and role in roles
