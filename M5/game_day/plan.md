# Plan du game day — DiagOps M5

Voir aussi le déroulé jour J : [`JOUR_J.md`](JOUR_J.md)  
Drill entraînement (courbe Prometheus) : `../pipelines/run_gameday_drill.sh`  
**Guide visuel (schémas)** : [`../docs/comprendre_m5.html`](../docs/comprendre_m5.html)

## Version saine et sauvegarde

| Élément | Valeur |
|---|---|
| Release saine | `diagops-m4-reference-r1` |
| Manifeste | `data_pack/.../m4_for_m5/release_manifest.json` |
| Archive locale | `artifacts/history/diagops-m4-reference-r1.json` (après seed) |
| Digests images | `docs/contrat_versions.md` |
| Sauvegarde | ne pas effacer `artifacts/history/` ni logs Prometheus pendant l'exercice |

Commande de restauration :

```bash
python3 pipelines/rollback_release.py diagops-m4-reference-r1 \
  --current artifacts/current.json \
  --history artifacts/history
```

## Candidat

| Élément | Valeur |
|---|---|
| Release candidate | `learner-candidate-gameday-v1` |
| Index | `artifacts/candidates/local/index.json` (`lexical-dfb8faf0c9b4`, 7 docs) |
| Gate | `artifacts/candidates/local/gate_report.json` → **passed** (rejoué 2026-09-07) |
| CI | `./pipelines/ci_local.sh` |
| Capacité | `artifacts/candidates/local/capacity_report.json` + `docs/rapport_capacite.md` |

Le candidat **ne remplace pas** la version saine tant que le game day n'a pas
validé la promotion (ou qu'une décision humaine explicite n'est prise).

## Rôles

| Rôle | Responsable | Mission |
|---|---|---|
| Incident commander | Apprenant (lead) | Chronométrer, décider rollback / continue |
| Observabilité | Apprenant (même poste solo) | Surveiller `/metrics`, Prometheus, ready |
| Exécutant rollback | Apprenant | Exécuter commandes runbook |
| Injecteur | Formateur / pair | Scénario sans toucher service externe |
| Scribe | Apprenant | Remplir `timeline.md` en direct |

En solo labo : les 3 premiers rôles sont tenus par la même personne ; l'injecteur reste externe.

## Canal de décision

- Terminal + journal `game_day/timeline.md`
- Décision verbale horodatée puis écrite (pas de chat externe requis)
- Seuil : si RTO estimé > 10 min ou perte de données → **arrêt contrôlé**

## Objectifs de service et de reprise

| Objectif | Cible formateur | Annonce équipe |
|---|---|---|
| Détection | &lt; 2 min | &lt; 2 min |
| Décision | &lt; 5 min | &lt; 5 min |
| Restauration | &lt; 10 min | &lt; 10 min |
| Perte de données | aucune | aucune (data_pack RO + history conservée) |
| Disponibilité ready | 503 détecté / traité | signal système, pas seulement animateur |

## Conditions d'arrêt

Arrêter l'exercice si :
1. corruption du `data_pack` (ne doit jamais arriver — volume RO) ;
2. perte de `artifacts/history` sans copie ;
3. dépassement 4 h phase incident sans restauration ni doc d'échec ;
4. escalade hors labo (accès réseau non prévu).

## Signaux attendus (par panne envisagée)

| Scénario | Signal système | Action |
|---|---|---|
| Index invalide | `diagops_index_valid 0` + ready 503 | Rollback / clear fault + rebuild candidat |
| Dépendance génération down | `diagops_dependency_up 0` + ready 503 | Qualifier ; rollback si promo liée |
| Gate citations / hit@3 KO | `gate_report.status=failed` | Refus promote |
| Latence retrieval | p95 capacité / healthcheck timeout | Réduire charge ; inspecter index |
| Config incompatible | ready 503 / validate_release error | Restaurer manifeste sain |
| Alerte manquante | ready 503 sans métrique | Remédiation : alerte + test |

## Procédure de rollback

Voir `docs/runbook.md` § Incident et `docs/rapport_rollback.md` (déjà exécuté en labo).

## Vérification après reprise

```bash
curl -s http://127.0.0.1:8000/health/ready
curl -s http://127.0.0.1:8000/version | python3 -c 'import sys,json; print(json.load(sys.stdin)["release_id"])'
python3 -m pytest -q
./pipelines/ci_local.sh
```

Attendu : ready 200, release saine ou candidat revalidé, pytest vert, gate passed.
