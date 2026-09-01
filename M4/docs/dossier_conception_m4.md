# Dossier de conception M4 — Brief online (CampusAtlas C1, C2, C4)

**Date :** 2026-08-31  
**Projet :** DiagOps — module 4  
**Décision observable :** *Peut-on déployer un modèle de provenance capteur et un assistant documentaire cité pour assister les techniciens maintenance, avec supervision humaine ?*

---

## 1. Besoin et décision observable

### Utilisateurs

| Rôle | Besoin | Décision assistée |
|---|---|---|
| Technicien | Consulter procédures (LOTO, seuils vibration/température) | Conduite à tenir sur une alerte |
| Superviseur | Valider données transmises à M4/M5 | Accepter ou retirer lignes synthétiques |
| Auditeur | Vérifier conformité agent + citations | Autoriser passage M5 |

### Erreurs coûteuses

1. **Faux négatif provenance** — laisser passer une mesure fabriquée comme réelle → analytics biaisés.
2. **Faux positif provenance** — exclure une mesure réelle → perte de couverture.
3. **Hallucination RAG** — réponse sans citation ou citation inventée → conduite dangereuse.
4. **Absence de refus** — répondre hors périmètre (panne future, donnée restreinte).

### Supervision humaine

- Seuils vibration/température : **revue humaine** explicite dans les procédures (DOC-PUMP-VIB-001).
- Agent M4 : **ne décide pas** de l'arrêt machine — 3 actions sans effet externe.

---

## 2. Données nécessaires

Voir `docs/tableau_donnees_necessaires.md`.

**Synthèse :** calibration capteurs (900 lignes, provenance visible), test scellé (1800 lignes), corpus 8 documents versionnés, 24 questions RAG. **Manquant :** oracles test, lot contradiction brief 2 (formateur).

**Périmètre de validité :** période `2026-S1`, données synthétiques formation — pas de généralisation industrielle directe.

---

## 3. Comparaison des familles de modèles

| Famille | Données | Explicabilité | Généralisation | Coût | Verdict M4 |
|---|---|---|---|---|---|
| **Règles (M3)** | Faible | Haute | Faible (rappel 0,27 cal.) | Très faible | Plancher obligatoire |
| **Supervisé (LR, RF)** | Calibration étiquetée | Moyenne (features + règles) | Moyenne | Faible | **Retenu** (RF F1 0,78) |
| **Non supervisé** | Non adapté | — | — | — | **Écarté** (pas de labels) |
| **Pré-entraîné (LLM)** | Corpus texte | Faible | Risquée | Élevé | **Reporté M5+** (RAG extractif d'abord) |

---

## 4. Protocole d'évaluation

Document détaillé : `docs/protocole_evaluation.md`.

- **Groupe :** `window_id` (30 mesures indivisibles).
- **Split :** calibration vs test scellé ; validation interne 80/20 par fenêtre.
- **Métriques capteur :** precision, recall, F1, ROC-AUC, latence.
- **Métriques RAG :** recall@k, taux abstention, exactitude citations.
- **Seuil :** battre baseline M3 en F1 sans régression recall > 10 pts sur validation.

---

## 5. Registre des risques

Voir `docs/registre_risques_online.md` et `docs/threat_model.md`.

| Risque | Atténuation | Résiduel |
|---|---|---|
| Fuite test | Gel candidat ; oracle hors dépôt | Hypothèse implicite dans features |
| Injection documentaire | Extraits = données | LLM génératif futur |
| Biais calibration | Segmenter par capteur | Distribution synthétique |
| AI Act | Supervision + traçabilité | Qualification juridique ouverte |

---

## 6. Recommandation finale (2026-08-31)

**Adopter sous conditions :**

1. **Modèle :** Random Forest sur features règles M3 + capteur — F1 calibration 0,78 vs 0,37 baseline.
2. **RAG :** retrieval **lexical-first** (correction brief 2) — recall@k 1,0, latence ~300 ms vs ~2900 ms vectoriel seul.
3. **Agent :** une étape, abstention testée.

**Ne pas conclure :** performance industrielle, prédiction panne, représentativité parc entier (M3 : 8,5 % couverture).

**Informations manquantes pouvant changer la décision :** métriques oracle test capteur et RAG (formateur).
