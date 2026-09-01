"""Explorateur DiagOps M3 — cartographie des jeux de données et retours pipeline."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

UI_DIR = Path(__file__).resolve().parent
if str(UI_DIR) not in sys.path:
    sys.path.insert(0, str(UI_DIR))

from datasets_catalog import PHASE_LABELS, catalog

ROOT = Path(__file__).resolve().parents[1]
DATA_PACK = ROOT / "../../data_pack/2026-S1"


def _find_repo_root() -> Path:
    for p in [ROOT, *ROOT.parents]:
        if (p / "data_pack" / "MANIFEST.yaml").is_file():
            return p
    return ROOT.parents[1]


REPO = _find_repo_root()
DATA_PACK = REPO / "data_pack" / "2026-S1"
OUTPUT = ROOT / "output"


@st.cache_data
def load_json(path: str) -> dict | list | None:
    p = Path(path)
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


@st.cache_data
def load_csv(path: str, nrows: int | None = 500) -> pd.DataFrame | None:
    p = Path(path)
    if not p.is_file():
        return None
    return pd.read_csv(p, nrows=nrows)


@st.cache_data
def db_table_counts(db_path: str) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    tables = pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
        conn,
    )["name"].tolist()
    rows = []
    for t in tables:
        n = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        rows.append({"table": t, "lignes": n})
    conn.close()
    return pd.DataFrame(rows)


def file_status(path: str) -> tuple[str, str]:
    p = Path(path)
    if not p.is_file():
        return "absent", "Fichier non généré — lancez le pipeline correspondant."
    size = p.stat().st_size
    if size > 1_000_000:
        label = f"{size / 1_000_000:.1f} Mo"
    elif size > 1_000:
        label = f"{size / 1_000:.0f} Ko"
    else:
        label = f"{size} o"
    return "présent", label


def page_overview() -> None:
    st.header("Cartographie des jeux de données")
    st.markdown(
        """
        Ce tableau relie **chaque fichier** à sa **phase de travail** et à son **rôle**
        dans le parcours DiagOps M3. Les fichiers du `data_pack/` sont en lecture seule ;
        tout le reste est produit par vos pipelines dans `work/M3/output/`.
        """
    )

    items = catalog(ROOT, DATA_PACK)
    rows = []
    for d in items:
        status, detail = file_status(d.path)
        rows.append(
            {
                "Phase": PHASE_LABELS.get(d.phase, d.phase),
                "Jeu de données": d.title,
                "Statut": f"{'✅' if status == 'présent' else '⬜'} {detail}",
                "Description": d.description,
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.subheader("Flux simplifié")
    st.code(
        """
data_pack/2026-S1/          →  output/processed/     →  output/brief2/
  equipment, events,           capteurs nettoyés,         génération SITE-OUEST,
  sensors (bruts)              quarantaine, alignment      verdicts, transmission M4
                                      │
                                      ▼
                               output/diagops.db (SQLite)
        """,
        language="text",
    )


def page_brief1() -> None:
    st.header("Brief 1 — Pipeline multi-source")
    report = load_json(str(OUTPUT / "validation_report.json"))
    if not report:
        st.warning("Lancez d'abord le pipeline : `launch.py` option 2 ou `python -m src.data_pipeline`.")
        return

    c1, c2, c3, c4 = st.columns(4)
    sensors = report.get("sensors", {})
    cov = report.get("coverage", {})
    align = report.get("alignment", {})
    c1.metric("Capteurs conservés", f"{sensors.get('kept', 0):,}")
    c2.metric("Exclus", f"{sensors.get('excluded', 0):,}")
    c3.metric("Couverture parc", f"{cov.get('coverage_rate', 0) * 100:.1f} %")
    c4.metric("Couples alignment", f"{align.get('alignment_rows', 0):,}")

    st.subheader("Décision")
    decision = report.get("decision", "—")
    st.info(f"**{decision}** — {report.get('decision_rationale', '')}")

    tab_src, tab_quar, tab_align, tab_raw = st.tabs(
        ["Sources", "Quarantaine", "Alignment", "Aperçu capteurs"]
    )
    with tab_src:
        st.json(report.get("sources", {}))
        st.caption("Empreintes SHA256 des fichiers bruts du data pack.")
    with tab_quar:
        q = load_csv(str(OUTPUT / "quarantine.csv"), nrows=200)
        if q is not None:
            st.write(f"**{len(q)}** lignes affichées (échantillon)")
            if "rule_id" in q.columns:
                st.bar_chart(q["rule_id"].value_counts())
            st.dataframe(q, use_container_width=True)
    with tab_align:
        a = load_csv(str(OUTPUT / "alignment/measures_events.csv"), nrows=300)
        if a is not None:
            st.dataframe(a.head(50), use_container_width=True)
    with tab_raw:
        s = load_csv(str(OUTPUT / "processed/sensor_readings.csv"), nrows=100)
        if s is not None:
            st.dataframe(s, use_container_width=True)


def page_db() -> None:
    st.header("Brief 1 online — Base SQLite")
    db = OUTPUT / "diagops.db"
    if not db.is_file():
        st.warning("Base absente — lancez `launch.py` option 6 (db_workflow).")
        return

    counts = db_table_counts(str(db))
    st.subheader("Tables")
    st.dataframe(counts, use_container_width=True, hide_index=True)

    queries = load_json(str(OUTPUT / "db/query_results.json"))
    if queries:
        st.subheader("Résultats requêtes documentées")
        for key, val in queries.items():
            with st.expander(key.replace("_", " ").title()):
                if isinstance(val, list):
                    st.dataframe(pd.DataFrame(val), use_container_width=True)
                else:
                    st.write(val)


def page_brief2() -> None:
    st.header("Brief 2 — Capacité et transmission M4")
    summary = load_json(str(OUTPUT / "brief2/brief2_summary.json"))
    if not summary:
        st.warning("Lancez d'abord le brief 2 : `launch.py` option 7.")
        return

    tx = summary.get("transmission_m4", {})
    st.success(f"**Décision : {tx.get('decision', '—')}**")

    c1, c2, c3 = st.columns(3)
    cap = summary.get("capacity", {})
    ver = summary.get("verdicts", {}).get("by_verdict", {})
    c1.metric("Couverture parc", f"{cap.get('coverage_rate', 0) * 100:.1f} %")
    c2.metric("Verdicts fabriquée", ver.get("fabriquée", 0))
    c3.metric("Lignes transmises M4", f"{tx.get('real_rows', 0):,} + {tx.get('synthetic_rows', 0)} synth.")

    tab_cap, tab_det, tab_lap, tab_tx = st.tabs(
        ["Capacité", "Détection", "Laplace", "Transmission M4"]
    )

    with tab_cap:
        st.markdown("**3 questions non traitables**")
        for q in cap.get("three_unanswerable_questions", []):
            st.markdown(f"- **{q['question']}** — {q['chiffre']}")
        by_site = pd.DataFrame(cap.get("by_site", []))
        if not by_site.empty:
            st.subheader("Couverture par site")
            st.bar_chart(by_site.set_index("site_id")["coverage"])

    with tab_det:
        verdicts = load_csv(str(OUTPUT / "brief2/verdicts_control_batch.csv"))
        if verdicts is not None:
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Par verdict**")
                st.bar_chart(verdicts["verdict"].value_counts())
            with col_b:
                st.markdown("**Par règle**")
                st.bar_chart(verdicts["rule_id"].value_counts().head(8))
            filt = st.selectbox(
                "Filtrer par verdict",
                ["Tous"] + sorted(verdicts["verdict"].unique().tolist()),
            )
            show = verdicts if filt == "Tous" else verdicts[verdicts["verdict"] == filt]
            st.dataframe(show.head(100), use_container_width=True)

        journal = load_json(str(OUTPUT / "brief2/detector_journal.json"))
        if journal:
            st.subheader("Journal détecteur de référence")
            for step in journal:
                rep = step.get("report", {})
                st.markdown(
                    f"**{step['step']}** — hypothèse : {step['hypothesis']}  \n"
                    f"Lignes signalées : **{rep.get('flagged_rows_total', '?')}**"
                )

    with tab_lap:
        lap = pd.DataFrame(summary.get("laplace", []))
        if not lap.empty:
            st.line_chart(lap.set_index("epsilon")["relative_error"])
            st.dataframe(lap, use_container_width=True)
            st.caption("Erreur relative vs ε — agrégat SITE-OUEST (16 équipements).")

    with tab_tx:
        st.markdown("**Conditions de transmission**")
        for cond in tx.get("conditions", []):
            st.markdown(f"- {cond}")
        m4 = load_csv(str(OUTPUT / "brief2/transmission_m4/sensor_readings_m4.csv"), nrows=50)
        if m4 is not None and "provenance" in m4.columns:
            st.bar_chart(m4["provenance"].value_counts())
            st.dataframe(m4.head(20), use_container_width=True)


def page_explorer() -> None:
    st.header("Explorateur de fichier")
    items = catalog(ROOT, DATA_PACK)
    labels = {d.id: d.title for d in items}
    choice = st.selectbox(
        "Choisir un jeu de données",
        options=[d.id for d in items],
        format_func=lambda i: labels[i],
    )
    info = next(d for d in items if d.id == choice)
    status, detail = file_status(info.path)

    st.markdown(f"**Chemin :** `{info.path}`")
    st.markdown(f"**Statut :** {status} ({detail})")
    st.markdown(info.description)
    if info.columns:
        st.caption(f"Colonnes : {info.columns}")
    if info.usage:
        st.caption(f"Usage : {info.usage}")

    p = Path(info.path)
    if not p.is_file():
        return

    if p.suffix == ".json":
        st.json(load_json(str(p)))
    elif p.suffix == ".csv":
        n = st.slider("Lignes à afficher", 10, 1000, 100, step=10)
        df = load_csv(str(p), nrows=n)
        if df is not None:
            st.write(f"Dimensions affichées : {len(df)} × {len(df.columns)}")
            st.dataframe(df, use_container_width=True)
    elif p.suffix == ".md":
        st.markdown(p.read_text(encoding="utf-8"))


def main() -> None:
    st.set_page_config(
        page_title="DiagOps M3 — Explorateur",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.sidebar.title("DiagOps M3")
    st.sidebar.caption("Comprendre les jeux de données et les retours pipeline")
    page = st.sidebar.radio(
        "Navigation",
        [
            "Vue d'ensemble",
            "Brief 1 — Pipeline",
            "Brief 1 online — DB",
            "Brief 2 — Capacité & M4",
            "Explorateur de fichier",
        ],
        label_visibility="collapsed",
    )

    st.sidebar.divider()
    st.sidebar.markdown("**Commandes utiles**")
    st.sidebar.code("python launch.py", language="bash")
    st.sidebar.code("streamlit run ui/explorer_app.py", language="bash")

    pages = {
        "Vue d'ensemble": page_overview,
        "Brief 1 — Pipeline": page_brief1,
        "Brief 1 online — DB": page_db,
        "Brief 2 — Capacité & M4": page_brief2,
        "Explorateur de fichier": page_explorer,
    }
    pages[page]()


if __name__ == "__main__":
    main()
