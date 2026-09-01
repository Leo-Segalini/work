# Qualification livraison candidate M2

**Décision :** `REJECTED`

16 anomalie(s) bloquante(s) — ne pas intégrer.

## Synthèse exécutive

- Intégrité fichiers (SHA-256) : conforme
- Volumes : 30 équipements (26 insertions, 4 mises à jour), 80 événements, 220 maintenances
- Anomalies bloquantes : **16** | Avertissements : 0
- Évolutions acceptables signalées : 1

## Anomalies par règle

| Règle | Occurrences | Interprétation |
|---|---:|---|
| `CAND-COLLISION` | 2 | Collision avec clés déjà publiées (historique immuable) |
| `CAND-DOM` | 3 | Valeur hors domaine métier (`contracts/schemas.py`) |
| `CAND-DUP` | 6 | Doublons d'identifiants dans le lot candidat |
| `CAND-FK` | 5 | Référence absente (équipement ou événement parent) |

## Évolutions acceptables

- `CAND-INFO` — source_system : colonne facultative nouvelle — évolution acceptable (valeur observée : `gmao-v2`)

## Réponses aux questions de qualification (1→10)

1. **Contrôles M2 réutilisables ?** Oui : schéma, domaines, FK et doublons provienent de `validation.py` ; seules les règles `CAND-*` comparent au socle publié.
2. **Écarts structurels ?** Colonne facultative `source_system` sur maintenance — signalée en `info`, non bloquante.
3. **Erreurs vs évolutions ?** Doublons, collisions, FK et domaines = erreurs ; `source_system` = évolution documentée.
4. **Règles versionnées ?** Voir `aller_plus_loin/config/quality_rules.yaml`.
5. **Seuils ?** Toute anomalie `block`/`quarantine` → rejet ; `warn` → acceptation sous conditions ; `info` → trace uniquement.
6. **Reproductibilité ?** `python scripts/qualify_candidate.py` + manifeste `aller_plus_loin/run_manifest.json`.
7. **Données publiées intactes ?** Oui — qualification en lecture seule, aucune fusion.
8. **Intégration sans altérer l'historique ?** Non — collisions `EVT-2026S1-0001` / `MNT-2026S1-0001` écraseraient des clés existantes.
9. **Reproduction ?** Checksums + comptages + 16 blocages reproductibles localement et en CI.
10. **Décision finale ?** **REJECTED** — corriger doublons, collisions, domaines et FK avant nouvelle soumission.

## GitHub Actions (11→16)

11. **Local vs CI ?** Mêmes commandes (`pytest`, audit socle, `qualify_candidate.py`) ; résultats identiques si `data_pack/` identique.
12. **Dépendances explicites ?** `requirements.lock`, `PYTHONPATH=.`, chemins relatifs vers `data_pack/`.
13. **Échec technique vs rejet métier ?** Job `socle` vert = pipeline OK ; job `candidate` avec `--strict` rouge = rejet métier attendu sur ce lot.
14. **Avertissements visibles ?** Décision `info`/`warn` dans le rapport sans faire échouer le job socle.
15. **Diagnostic sans relance ?** `qualification_report.json`, `candidate_findings.csv` et artefacts CI suffisent.
16. **Validation humaine ?** Arbitrage sur mises à jour équipement, PII sur notes, et toute exception aux domaines métier.

## Conditions de resoumission

- Supprimer les doublons (`EQ-M2X-002`, `EVT-2026S1-B002`, `MNT-2026S1-B0002`).
- Renommer ou retirer les lignes en collision avec l'historique publié.
- Normaliser les domaines (`urgent` → `critical`, `CRITICAL` → `critical`, `inspection` comme `intervention_type` et non `event_type`).
- Remplacer les références `EQ-UNKNOWN-999` / `EVT-UNKNOWN-999` ou créer les parents manquants.

*Généré le 2026-08-31T07:21:23Z — règles `CAND-*` + validation M2.*
