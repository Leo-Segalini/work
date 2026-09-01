"""Contenu pédagogique du brief M4 affiché dans l'explorateur."""

from __future__ import annotations

BRIEF_M4 = """
## Objectif du module M4

**Prouver avant d'architecturer.** DiagOps dispose déjà de données propres (M3) et de règles
de détection. M4 répond à deux questions mesurables :

1. **Un modèle simple** bat-il la baseline par règles M3 sur la **provenance** des mesures capteurs ?
2. **Un RAG cité** répond-il mieux aux questions maintenance qu'une réponse sans contexte ?

Ce n'est **pas** un module d'entraînement LLM générique : c'est une **démonstration scientifique**
avec jeux gelés, citations vérifiables et agent **borné** (une seule action, pas d'effet externe).
"""

OBJECTIFS = [
    {
        "titre": "Modèle capteur",
        "objectif": "Détecter les mesures fabriquées vs réelles",
        "pas": "Prédire une panne future (hors périmètre des données)",
        "preuve": "F1, recall, ROC-AUC vs baseline M3 sur calibration",
    },
    {
        "titre": "RAG documentaire",
        "objectif": "Répondre aux questions procédures avec citations",
        "pas": "Inventer une réponse plausible sans source",
        "preuve": "Recall@k, abstention, citations résolubles vers le manifeste",
    },
    {
        "titre": "Agent borné",
        "objectif": "Choisir : réponse directe, recherche doc, ou refus",
        "pas": "Boucle agentique, mémoire longue, écriture système",
        "preuve": "3 actions autorisées, tests de menaces",
    },
]

CHOIX_TECH = [
    {
        "composant": "scikit-learn",
        "usage": "Régression logistique + forêt aléatoire",
        "pourquoi": "Modèles interprétables, reproductibles, adaptés au volume (~900 lignes calibration)",
    },
    {
        "composant": "Baseline M3 (règles)",
        "usage": "Plancher à battre (M3-UNIT, M3-RANGE, etc.)",
        "pourquoi": "Figée dans le data pack — toute amélioration doit être démontrée",
    },
    {
        "composant": "Retrieval lexical",
        "usage": "Comptage de tokens (BM25-like maison)",
        "pourquoi": "Transparent, sans dépendance GPU, baseline obligatoire",
    },
    {
        "composant": "sentence-transformers / MiniLM",
        "usage": "Embeddings pour retrieval vectoriel",
        "pourquoi": "Index local reproductible ; modèle documenté dans configs/",
    },
    {
        "composant": "Pas de ChromaDB / LLM génératif",
        "usage": "—",
        "pourquoi": "Hors exigence M4 ; réponses extractives citées suffisent",
    },
    {
        "composant": "Features capteur",
        "usage": "Flags règles M3 + valeur + capteur one-hot",
        "pourquoi": "Le modèle apprend au-delà des règles sans casser la traçabilité",
    },
]

TYPES_DONNEES = [
    {
        "type": "Mesures capteurs (évaluation modèle)",
        "fichiers": "model_eval/sensor_calibration.csv, sensor_test.csv",
        "contenu": "Fenêtres de 30 mesures ; étiquette provenance (calibration) ; test sans label",
        "grain": "Ligne capteur, groupé par window_id",
    },
    {
        "type": "Corpus documentaire",
        "fichiers": "knowledge/manifest.csv + documents/DOC-*.md",
        "contenu": "Procédures maintenance (LOTO, vibration, température, accès données…)",
        "grain": "Document versionné (revision, checksum, rôles autorisés)",
    },
    {
        "type": "Questions RAG",
        "fichiers": "rag_eval/questions.jsonl",
        "contenu": "12 calibration + test scellé ; answerable true/false ; expected_document_ids",
        "grain": "Une question = un cas d'évaluation",
    },
    {
        "type": "Référence M3",
        "fichiers": "reference_runs/m3_for_m4/",
        "contenu": "Baseline règles figée, métriques de référence",
        "grain": "Règles M3-* par ligne capteur",
    },
    {
        "type": "Résultats M4 (générés)",
        "fichiers": "results/*.json, sensor_test_predictions.csv",
        "contenu": "Benchmarks, prédictions test, traces RAG calibration",
        "grain": "Rejouable via scripts/run_pipeline.py",
    },
]

FLUX = """
```
M3 (données + règles)
        │
        ▼
┌───────────────────────────────────────┐
│  M4 — Brief 1                         │
│  ├─ Modèle : LR / RF vs baseline M3   │
│  ├─ RAG : none → lexical → vectoriel  │
│  ├─ Citations + abstention            │
│  └─ Agent 1 étape + threat model      │
└───────────────────────────────────────┘
        │
        ▼
M5 (déploiement, monitoring — à venir)
```
"""

GLOSSAIRE = {
    "Provenance": "Origine d'une mesure : réelle (capteur usine) ou fabriquée (synthétique M3).",
    "window_id": "Groupe de 30 mesures consécutives — indivisible pour les splits train/val.",
    "Recall@k": "Part des questions où le bon document apparaît dans le top-k retrieval.",
    "Abstention": "Refus explicite quand le corpus ne permet pas de répondre.",
    "Citation": "Référence document_id + extrait vérifiable dans le manifeste.",
    "Baseline M3": "Ensemble de règles déterministes (unité, plage, format…) — plancher de performance.",
}
