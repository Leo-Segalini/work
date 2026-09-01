# Analyse AI Act — DiagOps M4

## Scénario A — Assistant documentaire maintenance (M4)

| Élément | Analyse |
|---|---|
| Rôle | Technicien consulte procédures via RAG cité |
| Supervision | Revue humaine sur seuils vibration/température ; agent ne décide pas l'arrêt |
| Traçabilité | Citations `document_id`, journal agent, abstention testée |
| Risque résiduel | Hallucination malgré citation ; injection indirecte dans corpus |

**Décision architecture :** maintenir agent sans boucle ; refus explicite ; pas d'outil à effet.

## Scénario B — Classification provenance capteurs

| Élément | Analyse |
|---|---|
| Rôle | Filtrer mesures fabriquées avant analytics |
| Impact | Erreur = fausse confiance sur données synthétiques |
| Atténuation | Provenance obligatoire M3 ; modèle = aide, pas source de vérité |

**Point ouvert M5 :** journaliser les prédictions en production.

## Incertitudes

- Classification exacte AI Act du POC — **validation juridique requise**.
- Extension agentique M6+ — réévaluer obligations.
