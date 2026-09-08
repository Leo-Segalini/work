# Journal de veille DiagOps — M5

> Ce journal n'est **pas** un avis juridique. Toute qualification AI Act / RGPD
> industrielle doit être validée par un responsable conformité.

## Passage de relais reçu (M4)

- Périmètre : assistant pédagogique maintenance, données synthétiques.
- Autonomie : une décision, aucun outil à effet externe.
- Points à vérifier en M5 : fournisseur d'inférence, localisation / sous-traitance,
  contenu et rétention des traces, accès opérateur, supervision humaine,
  incidents, documentation.
- Source relais : `data_pack/.../m4_for_m5/veille_diagops/` et `work/M4/veille_diagops/`.

---

## Entrée M5 — 2026-09-07

### Consultation

| Élément | Détail |
|---|---|
| Date | 2026-09-07 |
| Responsable entrée | Apprenant DiagOps S04 (work/M5) |
| Sources officielles | voir `sources_veille.md` |
| Périmètre examiné | Déploiement labo Compose, traces/métriques, rétention, supervision, incidents, promotion |

### Faits vérifiés (sources primaires)

1. **AI Act (Règlement UE 2024/1689)** — texte consolidé consulté via EUR-Lex
   (`CELEX:32024R1689` / consolidation `02024R1689-20260727`) :
   - documentation technique et tenue de registres pour systèmes à haut risque ;
   - journalisation / logs permettant la traçabilité lorsque le système y est soumis ;
   - procédures liées aux **incidents graves** et corrective actions côté fournisseurs
     concernés ;
   - la qualification « haut risque » **n'est pas tranchée** pour ce POC pédagogique.
2. **RGPD / minimisation** — principe de minimisation des données : les traces
   d'exploitation ne doivent pas contenir corpus documentaire ni données personnelles
   en clair (aligné CNIL « IA et données », consultation 2026-09-07).
3. **État technique M5** — stack locale, pas de fournisseur cloud d'inférence dans
   le starter ; référence extractive `diagops-grounded-reference-v1` ; data_pack en
   lecture seule.

### Analyse

| Thème | Constat labo M5 | Risque si non traité |
|---|---|---|
| Fournisseur / localisation | Inférence locale pédagogique ; pas de sous-traitant cloud dans Compose | Oublier de re-qualifier si un LLM cloud est branché plus tard |
| Traces | Métriques `diagops_*` sans contenu documentaire | Fuite PII / secret si prompts journalisés en clair |
| Rétention | 14 jours labo annoncés dans `monitoring/metrics.md` | Conflit avec obligations plus longues si reclassé haut risque |
| Supervision humaine | Promotion / rollback = décision humaine explicite | Auto-promote contournerait la supervision |
| Incidents | Runbook + `faults.json` + rapport rollback | Incident non chronométré / non documenté |
| Documentation | `contrat_versions`, runbook, gate reports | Impossible d'attribuer une réponse à une version |

### Décision M5

**`appliquer`** — traduire la veille dans les contrôles d'exploitation **sans**
augmenter l'autonomie de l'agent et **sans** qualification juridique définitive.

Contrôles modifiés / confirmés :

| Contrôle | Fichier | Effet |
|---|---|---|
| Gate bloquant avant promo | `configs/gates.json` + `pipelines/ci_local.sh` | Pas de livraison si qualité/citations/refus KO |
| Décision humaine de promotion | `docs/runbook.md` + `promote_release.py` | Production ≠ auto-CI |
| Minimisation des traces | `monitoring/metrics.md` + runbook | Interdiction corpus/PII dans labels |
| Rétention labo 14 j | `monitoring/metrics.md` | Accès superviseur ; revue M6 si prod réelle |
| Incident / rollback | `docs/runbook.md` + `docs/rapport_rollback.md` | Détection → décision → restauration vérifiable |
| Versions attribuables | `docs/contrat_versions.md` | Digests images + release_id |

### Incertitudes conservées

- Classification AI Act exacte du futur système industriel (scénario superviseur).
- Durée de rétention des logs si reclassement haut risque (ordres de grandeur
  réglementaires ≠ 14 j labo).
- Choix d'un fournisseur d'inférence cloud (localisation, DPA, transfert).

---

## Passage de relais M6

| Question ouverte | Responsable | Échéance |
|---|---|---|
| Valider juridiquement le scénario « superviseur / maintenance » (AI Act) | Lead DiagOps + conformité (à nommer) | Avant tout outil à effet (brief M6) |
| Décider rétention traces en environnement non pédagogique | Exploitant + DPO/conformité | Avant ouverture accès hors labo |
| Si LLM cloud : localisation, sous-traitance, clauses | Architecte M6 | Avant branchement fournisseur |
| Boucle feedback / réentraînement : ne jamais traiter une trace comme label auto | Équipe M6 | Dès introduction feedback |

**État transmis :** stack déployable, gates, runbook, rollback démontré, agent toujours borné.
