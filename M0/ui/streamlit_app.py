"""Interface Streamlit DiagOps M0."""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(Path(__file__).resolve().parents[1] / ".env")
REPORTS_PATH = ROOT / "data_pack" / "2026-S1" / "reports" / "reports.jsonl"
API_URL = os.getenv("DIAGOPS_API_URL", "http://127.0.0.1:8000").rstrip("/")


def load_reports() -> list[dict]:
    rows: list[dict] = []
    with REPORTS_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


st.set_page_config(page_title="DiagOps M0", layout="centered")
st.title("DiagOps — Diagnostic maintenance")
st.caption("Soumettez un rapport technicien pour obtenir un diagnostic structuré.")

reports = load_reports()
if len(reports) < 3:
    st.error("Au moins 3 rapports sont attendus dans le data pack.")
    st.stop()

labels = [
    f"{row['report_id']} — {row['technician_note'][:60]}…" for row in reports
]
choice = st.selectbox(
    "Rapport du data pack",
    options=range(len(reports)),
    format_func=lambda index: labels[index],
)
selected = reports[choice]

report_id = st.text_input("report_id", value=selected["report_id"])
equipment_id = st.text_input(
    "equipment_id",
    value=selected.get("equipment_id") or "",
)
note = st.text_area(
    "technician_note",
    value=selected["technician_note"],
    height=160,
)

if st.button("Diagnostiquer", type="primary"):
    payload = {
        "report_id": report_id,
        "technician_note": note,
        "equipment_id": equipment_id or None,
    }
    try:
        response = httpx.post(f"{API_URL}/diagnose", json=payload, timeout=90.0)
        if response.status_code == 200:
            st.success("Diagnostic reçu")
            st.json(response.json())
        else:
            st.error(f"Erreur {response.status_code}")
            try:
                st.write(response.json())
            except ValueError:
                st.write(response.text)
    except httpx.HTTPError as exc:
        st.error(f"Impossible de joindre l'API : {exc}")
