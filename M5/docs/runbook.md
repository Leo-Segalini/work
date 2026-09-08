# Runbook DiagOps M5

## Responsables et escalade

| Rôle | Responsable | Canal |
|---|---|---|
| Exploitant labo | Apprenant M5 | Journal de bord + terminal |
| Décision promotion / rollback | Apprenant M5 (humain explicite) | `promote_release` / `rollback_release` |
| Escalade formateur | Formateur S04 | Incident game day |

## Démarrage et test de fumée

```bash
cd work/M5
source .venv/bin/activate
docker compose -f deploy/compose.yaml up --build -d
curl -s http://127.0.0.1:8000/health/live    # {"status":"live"}
curl -s http://127.0.0.1:8000/health/ready   # ready + release_id
curl -s http://127.0.0.1:8000/version
curl -s http://127.0.0.1:8000/metrics | grep diagops_
# Prometheus UI : http://127.0.0.1:9090
```

Attendu : API `healthy`, cible Prometheus `up`, `diagops_ready 1`.

## Arrêt contrôlé

```bash
docker compose -f deploy/compose.yaml down
# Conserver le volume artefacts si besoin d'historique :
# docker volume ls | grep diagops
```

## Construction et publication d'un index

```bash
./pipelines/ci_local.sh
# Produit artifacts/candidates/local/{index.json,gate_report.json}
# Promotion UNIQUEMENT si gate passed et décision humaine :
python3 pipelines/promote_release.py \
  --candidate artifacts/candidates/local/release.json \
  --gate artifacts/candidates/local/gate_report.json \
  --current artifacts/current.json \
  --history artifacts/history
```

Atomicité : l'index candidat n'écrase jamais le data_pack ni le slot sain ; `atomic_write_json` pour current.

## Incident et rollback

1. Signaux : `/health/ready` 503, `diagops_index_valid 0`, gate `failed`.
2. Décider en &lt; 5 min (objectif formateur).
3. Restaurer :

```bash
python3 pipelines/rollback_release.py diagops-m4-reference-r1 \
  --current artifacts/current.json \
  --history artifacts/history
```

4. Vérifier fumée + pytest. Voir `docs/rapport_rollback.md`.

Injection labo (ne pas laisser en place) :

```bash
docker compose -f deploy/compose.yaml exec -T api python -c \
  "from pathlib import Path; Path('artifacts/runtime').mkdir(parents=True, exist_ok=True); Path('artifacts/runtime/faults.json').write_text('{\"index_valid\": false}')"
```

## Sauvegarde, restauration et rotation des secrets

- Pas de secrets dans l'image ni le dépôt (référence pédagogique sans token).
- Sauvegarde = `artifacts/history/*.json` + digests dans `docs/contrat_versions.md`.
- Rotation : N/A labo ; en réel, secrets via env hors Compose file commité.

## Traces, accès et rétention

- Métriques techniques uniquement (pas de corpus/PII dans labels).
- Rétention labo : 14 jours ; accès superviseur.
- Politique détaillée : `monitoring/metrics.md`.
- **Veille M5 (2026-09-07) :** toute extension de journalisation (prompts, réponses,
  documents) exige une nouvelle entrée de veille et une décision explicite ; voir
  `veille_diagops/journal_veille.md`.

## Lien réglementaire (contrôle)

Avant chaque promotion de candidat hors labo personnel :

1. Vérifier que le gate est `passed`.
2. Vérifier l'absence de secret / document sensible dans les artefacts.
3. Confirmer qu'aucune action agent hors liste n'a été ajoutée.
4. Consulter la dernière entrée de `veille_diagops/` si fournisseur ou rétention change.
