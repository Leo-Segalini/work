# Registre des risques — Brief online M4

| ID | Risque | Impact | Probabilité | Atténuation | Résiduel | Owner |
|---|---|---|---|---|---|---|
| R1 | Faux négatif provenance | Analytics biaisés | Moyenne | RF + règles combinées | Test scellé non vu | Data |
| R2 | Hallucination RAG | Conduite incorrecte | Moyenne | Citations obligatoires + abstention | Interprétation extractive | RAG |
| R3 | Injection indirecte | Override agent | Faible | 3 actions, pas d'écriture | LLM futur | Sécurité |
| R4 | Fuite calibration→test | Sur-apprentissage | Faible | window_id groupé | Features implicites | ML |
| R5 | Non-conformité AI Act | Obligations légales | Incertaine | Veille + supervision | Validation juridique | Conformité |
| R6 | Latence RAG vectoriel | UX / coût | Élevée | Politique lexical-first (B2) | Questions sémantiques rares | Ops |

**Communication :** risques R1–R3 documentés dans `threat_model.md` ; R5 dans `veille_diagops/ai_act_diagops.md`.
