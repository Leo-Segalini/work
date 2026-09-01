# Preuve individuelle M1

## Identification

- apprenant : segalini-briant (solo)
- groupe : solo Mac
- commit : *à renseigner*

## Contribution

- rôle principal : pilote expérimental + opérateur + analyste (rôles cumulés)
- hypothèse ou configuration prise en charge : variation_1 (r=8) et protocole Mac hybride
- run exécuté ou reproduit : init splits/env ; configs renseignées avant run ; smoke Mac best-effort

## Deux erreurs analysées

### Erreur 1

- identifiant : risque méthodologique M-01
- observation : tenter d'utiliser un smoke Mac comme preuve de promotion
- cause probable : confusion entre exécutabilité locale et protocole GPU commun
- impact : décision biaisée → corrigé par séparation smoke / référence

### Erreur 2

- identifiant : risque M-02 (issu de M0)
- observation : sévérité souvent lissée à `medium` sur modèles non spécialisés
- cause probable : calibrage faible / corpus synthétique
- impact : seuil macro-F1 severity du Brief 2 peut échouer → à vérifier sur LoRA GPU

## Objection traitée

- objection : les métriques Mac smoke suffisent-elles ?
- preuve : brief M1 + `peer_review.md`
- réponse : non — prolonger jusqu'au run GPU de référence

## Intégration

- candidat chargé : *après smoke / adaptateur*
- commande ou test exécuté : `POST /diagnose` via provider configurable M0
- résultat de `/diagnose` : *à joindre après test d'intégration*

## Recommandation

- **prolonger**
- justification : dossier méthodologique prêt ; preuves quantitatives GPU absentes ; smoke Mac non comparable
