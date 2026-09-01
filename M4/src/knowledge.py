"""Chargement du corpus documentaire versionné."""

from __future__ import annotations

from pathlib import Path

from .io_contracts import load_manifest


def load_corpus(manifest_path: Path, documents_dir: Path) -> list[dict]:
    rows = load_manifest(manifest_path, documents_dir)
    corpus = []
    for meta in rows:
        text = (documents_dir / meta["asset_path"]).read_text(encoding="utf-8")
        corpus.append(
            {
                "document_id": meta["document_id"],
                "title": meta["title"],
                "revision": meta["revision"],
                "status": meta["status"],
                "sensitivity": meta["sensitivity"],
                "allowed_roles": meta["allowed_roles"],
                "supersedes_document_id": meta.get("supersedes_document_id") or "",
                "text": text,
                "metadata": meta,
            }
        )
    return corpus


def admissible_documents(corpus: list[dict], role: str) -> list[dict]:
    from .retrieval import admissible

    return [doc for doc in corpus if admissible(doc["metadata"], role)]
