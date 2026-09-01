# Support de défense — Brief 2 M4

## Décision finale révisée

**Adopter :**
- Random Forest pour provenance capteur (calibration F1 0,78)
- Retrieval **lexical-first** pour RAG (même recall@k, latence ÷4000)

**Maintenir sous conditions :**
- Baseline M3 comme plancher de secours
- Validation test scellé formateur avant M5

## Meilleur argument contraire

> « Le RF n'a pas prouvé sa valeur sur le test scellé ; le lexical-first pourrait échouer sur des questions sémantiques hors vocabulaire partagé. »

**Réponse :** acceptée comme risque résiduel — repli vectoriel conservé ; décision M5 conditionnée aux métriques formateur.

## Gate M4

- [x] Correction unique attribuable (lexical-first)
- [x] Menaces étendues testées
- [x] Qualification lot test documentée
- [ ] Reproduction par pair (phase 2 — présentiel)
