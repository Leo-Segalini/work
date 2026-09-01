"""Explorateur DiagOps M4 — brief, données et résultats."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

UI_DIR = Path(__file__).resolve().parent
if str(UI_DIR) not in sys.path:
    sys.path.insert(0, str(UI_DIR))

from brief_content import BRIEF_M4, CHOIX_TECH, FLUX, GLOSSAIRE, OBJECTIFS, TYPES_DONNEES
from datasets_catalog import PHASE_LABELS, catalog

ROOT = Path(__file__).resolve().parents[1]


def _find_repo_root() -> Path:
    for p in [ROOT, *ROOT.parents]:
        if (p / "data_pack" / "MANIFEST.yaml").is_file():
            return p
    return ROOT.parents[1]


REPO = _find_repo_root()
DATA_PACK = REPO / "data_pack" / "2026-S1"
RESULTS = ROOT / "results"
DOCS = ROOT / "docs"


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
def load_jsonl(path: str) -> list[dict]:
    p = Path(path)
    if not p.is_file():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def file_status(path: str) -> tuple[str, str]:
    p = Path(path)
    if not p.is_file():
        return "absent", "Non généré — lancez le pipeline."
    size = p.stat().st_size
    if size > 1_000_000:
        label = f"{size / 1_000_000:.1f} Mo"
    elif size > 1_000:
        label = f"{size / 1_000:.0f} Ko"
    else:
        label = f"{size} o"
    return "présent", label


def page_brief() -> None:
    st.header("Brief M4 — Comprendre le projet")
    st.markdown(BRIEF_M4)

    st.subheader("Les 3 axes de travail")
    for obj in OBJECTIFS:
        with st.expander(obj["titre"], expanded=True):
            st.markdown(f"**Objectif :** {obj['objectif']}")
            st.markdown(f"**Ce n'est pas :** {obj['pas']}")
            st.markdown(f"**Preuve attendue :** {obj['preuve']}")

    st.subheader("Choix techniques")
    st.dataframe(
        pd.DataFrame(CHOIX_TECH)[["composant", "usage", "pourquoi"]],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Types de données")
    st.dataframe(
        pd.DataFrame(TYPES_DONNEES),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Flux du parcours")
    st.code(FLUX.strip(), language="text")

    st.subheader("Glossaire")
    for term, definition in GLOSSAIRE.items():
        st.markdown(f"**{term}** — {definition}")

    summary = load_json(str(RESULTS / "m4_summary.json"))
    if summary:
        st.success("Pipeline exécuté — voir les onglets Modèle et RAG pour les chiffres.")
    else:
        st.info("Lancez `PYTHONPATH=. python scripts/run_pipeline.py` pour générer les résultats.")


def page_catalog() -> None:
    st.header("Catalogue des jeux de données")
    items = catalog(ROOT, DATA_PACK)
    rows = []
    for d in items:
        status, detail = file_status(d.path)
        rows.append(
            {
                "Phase": PHASE_LABELS.get(d.phase, d.phase),
                "Jeu": d.title,
                "Statut": f"{'✅' if status == 'présent' else '⬜'} {detail}",
                "Description": d.description,
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.subheader("Contenu des documents corpus")
    manifest_path = DATA_PACK / "knowledge/manifest.csv"
    if manifest_path.is_file():
        manifest = pd.read_csv(manifest_path)
        st.dataframe(
            manifest[["document_id", "title", "revision", "status", "allowed_roles"]],
            use_container_width=True,
            hide_index=True,
        )


def page_model() -> None:
    st.header("Modèle capteur — provenance")
    st.markdown(
        "**Cible :** distinguer mesures **réelles** vs **fabriquées**. "
        "Ce n'est pas une prédiction de panne."
    )

    summary = load_json(str(RESULTS / "m4_summary.json"))
    if not summary:
        st.warning("Exécutez d'abord `scripts/run_pipeline.py`.")
        return

    model = summary["model"]
    base = model["baseline_m3_calibration"]
    best = model["selected_model"]
    cand = model["candidates"][best]["calibration_full"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fenêtres calibration", model["calibration_windows"])
    c2.metric("F1 baseline M3", f"{base['f1']:.3f}")
    c3.metric(f"F1 {best}", f"{cand['f1']:.3f}")
    c4.metric("Modèle retenu", best.replace("_", " ").title())

    tab_cmp, tab_data, tab_pred = st.tabs(["Comparaison", "Données calibration", "Prédictions test"])

    with tab_cmp:
        cmp = pd.DataFrame(
            [
                {"Système": "Baseline M3", "Precision": base["precision"], "Recall": base["recall"], "F1": base["f1"]},
                {"Système": "Logistic Regression", **model["candidates"]["logistic_regression"]["calibration_full"]},
                {"Système": "Random Forest", **model["candidates"]["random_forest"]["calibration_full"]},
            ]
        )[["Système", "precision", "recall", "f1"]].rename(
            columns={"precision": "Precision", "recall": "Recall", "f1": "F1"}
        )
        st.bar_chart(cmp.set_index("Système")[["F1"]])
        st.dataframe(cmp, use_container_width=True, hide_index=True)

        st.markdown("**Matrice de confusion — baseline M3 (calibration)**")
        cm = base["confusion_matrix"]
        st.dataframe(
            pd.DataFrame(cm, index=["Vrai réelle", "Vrai fabriquée"], columns=["Pred réelle", "Pred fabriquée"]),
            use_container_width=True,
        )

    with tab_data:
        cal = load_csv(str(DATA_PACK / "model_eval/sensor_calibration.csv"))
        if cal is not None:
            st.bar_chart(cal["provenance"].value_counts())
            st.dataframe(cal.head(50), use_container_width=True)

    with tab_pred:
        pred = load_csv(str(RESULTS / "sensor_test_predictions.csv"), nrows=200)
        if pred is not None:
            st.bar_chart(pred["prediction"].value_counts())
            st.dataframe(pred.head(30), use_container_width=True)
            st.caption("Test sans oracle local — métriques finales : formateur.")


def page_rag() -> None:
    st.header("RAG — retrieval et réponses citées")
    st.markdown(
        "Compare **sans retrieval**, **lexical** et **vectoriel**. "
        "Chaque réponse doit citer un `document_id` ou **refuser**."
    )

    summary = load_json(str(RESULTS / "m4_summary.json"))
    if not summary:
        st.warning("Exécutez d'abord `scripts/run_pipeline.py`.")
        return

    rag = summary["rag"]
    st.info(f"Modèle embeddings : `{rag['embedding_model']}` — {rag['corpus_documents']} documents")

    strategies = rag.get("strategies", {})
    if strategies:
        df = pd.DataFrame(strategies).T.reset_index().rename(columns={"index": "Stratégie"})
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.bar_chart(df.set_index("Stratégie")[["recall_at_k"]])

    results = load_jsonl(str(RESULTS / "rag_calibration_results.jsonl"))
    if results:
        df_r = pd.DataFrame(results)
        st.subheader("Détail par question (calibration)")
        strat = st.selectbox("Stratégie", sorted(df_r["strategy"].unique()))
        show = df_r[df_r["strategy"] == strat][
            ["eval_id", "abstained", "outcome", "retrieved_ids", "agent_action"]
        ]
        st.dataframe(show, use_container_width=True)

        q_pick = st.selectbox("Question détaillée", show["eval_id"].tolist())
        row = df_r[(df_r["eval_id"] == q_pick) & (df_r["strategy"] == strat)].iloc[0]
        st.markdown(f"**Réponse :** {row['answer']}")
        st.markdown(f"**Citations :** {row['citations']}")
        st.markdown(f"**Agent :** `{row['agent_action']}` — {row['agent_rationale']}")


def page_brief_online() -> None:
    st.header("Brief online — Dossier de conception")
    doc = DOCS / "dossier_conception_m4.md"
    if doc.is_file():
        st.markdown(doc.read_text(encoding="utf-8"))
    for extra in ("tableau_donnees_necessaires.md", "registre_risques_online.md"):
        p = DOCS / extra
        if p.is_file():
            with st.expander(extra.replace("_", " ").replace(".md", "")):
                st.markdown(p.read_text(encoding="utf-8"))


def page_brief2() -> None:
    st.header("Brief 2 — Réplication et correction")
    summary = load_json(str(RESULTS / "brief2_summary.json"))
    if not summary:
        st.warning("Lancez `scripts/run_brief2.py`.")
        return
    corr = summary.get("correction", {})
    c1, c2, c3 = st.columns(3)
    c1.metric("Latence avant (vector)", f"{corr.get('before', {}).get('avg_latency_ms', 0):.0f} ms")
    c2.metric("Latence après (lexical-first)", f"{corr.get('after', {}).get('avg_latency_ms', 0):.2f} ms")
    c3.metric("Transmissible", "Oui" if summary["audit"].get("transmissible") else "Partiel")

    st.markdown(f"**Correction :** {corr.get('change', '—')}")
    st.markdown(f"**Décision révisée :** {summary.get('decision_revised', '—')}")

    for name in (
        "../approfondissement/qualification_nouveau_lot.md",
        "../approfondissement/remediation.md",
        "../approfondissement/defense.md",
    ):
        p = ROOT / name.replace("../", "")
        if p.is_file():
            with st.expander(p.name):
                st.markdown(p.read_text(encoding="utf-8"))


def page_agent_threats() -> None:
    st.header("Agent borné et menaces")
    st.markdown(
        """
        L'agent M4 choisit **une seule action** :
        - `answer_without_tool`
        - `search_knowledge`
        - `abstain`

        Pas de boucle, pas d'écriture, pas d'effet sur un système externe.
        """
    )

    threat_path = DOCS / "threat_model.md"
    if threat_path.is_file():
        st.markdown(threat_path.read_text(encoding="utf-8"))

    matrice = DOCS / "matrice_decision.md"
    if matrice.is_file():
        st.subheader("Décision")
        st.markdown(matrice.read_text(encoding="utf-8"))


def page_explorer() -> None:
    st.header("Explorateur de fichier")
    items = catalog(ROOT, DATA_PACK)
    labels = {d.id: d.title for d in items}
    choice = st.selectbox(
        "Jeu de données",
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

    p = Path(info.path)
    if not p.is_file():
        return
    if p.suffix == ".json":
        st.json(load_json(str(p)))
    elif p.suffix == ".csv":
        n = st.slider("Lignes", 10, 500, 50, 10)
        df = load_csv(str(p), nrows=n)
        if df is not None:
            st.dataframe(df, use_container_width=True)
    elif p.suffix == ".jsonl":
        rows = load_jsonl(str(p))[:50]
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    elif p.suffix == ".md":
        st.markdown(p.read_text(encoding="utf-8"))


def main() -> None:
    st.set_page_config(
        page_title="DiagOps M4 — Explorateur",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.sidebar.title("DiagOps M4")
    st.sidebar.caption("Brief, données et résultats du module")
    page = st.sidebar.radio(
        "Navigation",
        [
            "Brief du projet",
            "Brief online (conception)",
            "Catalogue données",
            "Modèle capteur",
            "RAG documentaire",
            "Brief 2 — correction",
            "Agent & menaces",
            "Explorateur fichier",
        ],
        label_visibility="collapsed",
    )

    st.sidebar.divider()
    st.sidebar.markdown("**Commandes**")
    st.sidebar.code("python scripts/run_pipeline.py", language="bash")
    st.sidebar.code("streamlit run ui/explorer_app.py", language="bash")

    pages = {
        "Brief du projet": page_brief,
        "Brief online (conception)": page_brief_online,
        "Catalogue données": page_catalog,
        "Modèle capteur": page_model,
        "RAG documentaire": page_rag,
        "Brief 2 — correction": page_brief2,
        "Agent & menaces": page_agent_threats,
        "Explorateur fichier": page_explorer,
    }
    pages[page]()


if __name__ == "__main__":
    main()
