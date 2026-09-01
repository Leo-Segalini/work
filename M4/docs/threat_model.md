# Threat model M4

| ID | Attaque | Détection | Atténuation | Risque résiduel |
|---|---|---|---|---|
| T-INJECT-001 | Instruction malveillante dans un document | Le contenu récupéré est traité comme donnée, jamais comme instruction | Contrat DOC-RAG-OPS-001 + pas d'exécution d'instructions extraites | Modèle génératif externe pourrait encore suivre une injection |
| T-OBSOLETE-001 | Document obsolète mais présent (DOC-LOTO-001 superseded) | Filtre status=active via admissible() | Exclure superseded ; signaler conflit de révision | Erreur de manifeste non détectée |
| T-CONFLICT-001 | Sources contradictoires (révisions LOTO) | risk_tags conflict / obsolete_source | Citer les deux révisions et prioriser la active | Conflits non tagués dans les questions |
| T-SENSITIVE-001 | Question demandant une donnée restreinte (rôle public) | admissible() exclut docs restreints pour public | Abstention ou réponse policy DOC-DATA-ACCESS-001 | Fuite par agrégat indirect |
| T-BYPASS-001 | Forcer l'agent à ignorer ses limites | validate_decision — 3 actions seulement | Agent sans boucle ni outil d'écriture | Prompt injection sur LLM si branché en M5+ |
| T-INCOMPLETE-001 | Corpus incomplet (question hors périmètre) | answerable=false ou retrieval vide | Abstention explicite | Faux refus si index mal construit |

## Vérifications automatiques

```json
[
  {
    "case": "T-SENSITIVE-001",
    "check": "public cannot access restricted doc",
    "passed": true
  },
  {
    "case": "T-BYPASS-001",
    "check": "no evidence -> abstain",
    "passed": true
  },
  {
    "case": "T-INJECT-001",
    "check": "unknown citation rejected",
    "passed": true
  },
  {
    "case": "T-INCOMPLETE-001",
    "check": "abstention has no citation",
    "passed": true
  }
]
```
