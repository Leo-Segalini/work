"""Cas de menace documentés pour le threat model M4."""

from __future__ import annotations

from .bounded_agent import decide
from .contracts import Citation, GroundedAnswer
from .grounded_answer import abstain, validate_citations
from .retrieval import admissible


THREAT_CASES = [
    {
        "id": "T-INJECT-001",
        "attack": "Instruction malveillante dans un document",
        "detection": "Le contenu récupéré est traité comme donnée, jamais comme instruction",
        "mitigation": "Contrat DOC-RAG-OPS-001 + pas d'exécution d'instructions extraites",
        "residual": "Modèle génératif externe pourrait encore suivre une injection",
    },
    {
        "id": "T-OBSOLETE-001",
        "attack": "Document obsolète mais présent (DOC-LOTO-001 superseded)",
        "detection": "Filtre status=active via admissible()",
        "mitigation": "Exclure superseded ; signaler conflit de révision",
        "residual": "Erreur de manifeste non détectée",
    },
    {
        "id": "T-CONFLICT-001",
        "attack": "Sources contradictoires (révisions LOTO)",
        "detection": "risk_tags conflict / obsolete_source",
        "mitigation": "Citer les deux révisions et prioriser la active",
        "residual": "Conflits non tagués dans les questions",
    },
    {
        "id": "T-SENSITIVE-001",
        "attack": "Question demandant une donnée restreinte (rôle public)",
        "detection": "admissible() exclut docs restreints pour public",
        "mitigation": "Abstention ou réponse policy DOC-DATA-ACCESS-001",
        "residual": "Fuite par agrégat indirect",
    },
    {
        "id": "T-BYPASS-001",
        "attack": "Forcer l'agent à ignorer ses limites",
        "detection": "validate_decision — 3 actions seulement",
        "mitigation": "Agent sans boucle ni outil d'écriture",
        "residual": "Prompt injection sur LLM si branché en M5+",
    },
    {
        "id": "T-INCOMPLETE-001",
        "attack": "Corpus incomplet (question hors périmètre)",
        "detection": "answerable=false ou retrieval vide",
        "mitigation": "Abstention explicite",
        "residual": "Faux refus si index mal construit",
    },
]


def run_threat_checks() -> list[dict]:
    """Vérifie programmatiquement quelques atténuations."""
    results = []
    meta_public = {"status": "active", "allowed_roles": "public"}
    meta_restricted = {"status": "active", "allowed_roles": "superviseur;auditeur"}
    results.append(
        {
            "case": "T-SENSITIVE-001",
            "check": "public cannot access restricted doc",
            "passed": not admissible(meta_restricted, "public")
            and admissible(meta_public, "public"),
        }
    )
    decision = decide(needs_documents=False, answerable_without_tool=False, query="")
    results.append(
        {
            "case": "T-BYPASS-001",
            "check": "no evidence -> abstain",
            "passed": decision.action == "abstain",
        }
    )
    forged = GroundedAnswer(
        answer="x",
        citations=(Citation("DOC-FAUX", "y"),),
    )
    results.append(
        {
            "case": "T-INJECT-001",
            "check": "unknown citation rejected",
            "passed": bool(validate_citations(forged, {"DOC-LOTO-002"})),
        }
    )
    abst = abstain("ok")
    results.append(
        {
            "case": "T-INCOMPLETE-001",
            "check": "abstention has no citation",
            "passed": validate_citations(abst, set()) == [],
        }
    )
    return results
