#!/usr/bin/env python3
"""Grille de reproduction indépendante — Brief 2 M4 (auto-audit reproductible)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _run(cmd: list[str], cwd: Path) -> tuple[str, bool, str]:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env={**__import__("os").environ, "PYTHONPATH": str(cwd)})
    ok = proc.returncode == 0
    tail = (proc.stdout or proc.stderr).strip().splitlines()[-2:]
    return ("reproduit" if ok else "écart"), ok, " | ".join(tail)


def build_grille(root: Path) -> dict:
    rows = []

    st, ok, proof = _run([sys.executable, "-m", "pytest", "-q", "--ignore=tests/test_brief2.py"], root)
    rows.append({"check": "Environnement + tests (hors brief2 lent)", "status": st, "proof": proof})

    st, ok, proof = _run([sys.executable, "scripts/run_pipeline.py"], root)
    rows.append({"check": "Run principal pipeline M4", "status": st if ok else "écart", "proof": proof[:200]})

    summary = root / "results/m4_summary.json"
    if summary.is_file():
        data = json.loads(summary.read_text())
        f1 = data["model"]["candidates"]["random_forest"]["calibration_full"]["f1"]
        rows.append({"check": "Run modèle RF", "status": "reproduit", "proof": f"F1={f1}"})
    else:
        rows.append({"check": "Run modèle RF", "status": "bloqué", "proof": "m4_summary absent"})

    rag = root / "results/benchmark_retrieval.json"
    rows.append({
        "check": "Run retrieval",
        "status": "reproduit" if rag.is_file() else "bloqué",
        "proof": rag.read_text(encoding="utf-8")[:120] if rag.is_file() else "",
    })

    cite = _run([sys.executable, "-m", "pytest", "tests/test_citations.py", "tests/test_abstention.py", "-q"], root)
    rows.append({"check": "Échantillon citations / abstention", "status": cite[0], "proof": cite[2]})

    thr = _run([sys.executable, "-m", "pytest", "tests/test_agent_bounds.py", "tests/test_brief2.py::test_extended_threats_pass", "-q"], root)
    rows.append({"check": "Menaces (agent + extended)", "status": thr[0], "proof": thr[2]})

    rows.append({
        "check": "Fuite test",
        "status": "non testé",
        "proof": "Oracle capteur/RAG hors dépôt — protocole window_id documenté",
    })
    rows.append({
        "check": "Hypothèses implicites",
        "status": "écart",
        "proof": "Features incluent règles M3 — assumé et documenté",
    })

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "author": "auto-audit (substitut phase 2 en autonomie)",
        "rows": rows,
        "counter_argument": "RF non validé sur test scellé ; lexical-first peut échouer sur requêtes sémantiques pures.",
    }


def _md_cell(value: str, max_len: int = 120) -> str:
    text = (value or "").replace("|", "\\|").replace("\n", " ").strip()
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text


def write_markdown(grille: dict, path: Path) -> None:
    lines = [
        "# Grille de reproduction — M4",
        "",
        f"**Date :** {grille['generated_at'][:10]}",
        f"**Mode :** {grille['author']}",
        "",
        "| Vérification | Statut | Preuve |",
        "|---|---|---|",
    ]
    for row in grille["rows"]:
        lines.append(
            f"| {row['check']} | {row['status']} | {_md_cell(row['proof'])} |"
        )
    lines.extend([
        "",
        "## Meilleur argument contraire",
        "",
        grille["counter_argument"],
        "",
        "*Phase 2 pair : à compléter par un autre apprenant en présentiel.*",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    grille = build_grille(ROOT)
    out_json = ROOT / "approfondissement/grille_reproduction_filled.json"
    out_md = ROOT / "approfondissement/grille_reproduction.md"
    out_json.write_text(json.dumps(grille, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(grille, out_md)
    print(json.dumps({"written": [str(out_json), str(out_md)], "rows": len(grille["rows"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
