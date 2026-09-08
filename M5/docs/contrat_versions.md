# Contrat de versions — DiagOps M5

**Release saine figée :** `diagops-m4-reference-r1`  
**Périmètre :** `pedagogical_preproduction_only`  
**Source :** `data_pack/2026-S1/reference_runs/m4_for_m5/release_manifest.json`  
**Règle :** un tag d'image mutable n'est **pas** une version de restauration. Toujours relever le digest après build.

## Unités liées (version saine)

| Unité | Version | Checksum ou digest | Source | Compatible avec | Procédure de retour |
|---|---|---|---|---|---|
| Release | `diagops-m4-reference-r1` | manifeste JSON `schema_version=1` | `release_manifest.json` | toutes les lignes ci-dessous | pointer `DIAGOPS_REFERENCE_MANIFEST` vers ce manifeste ; `rollback_release` vers ce `release_id` |
| Code baseline | `m4-baseline-r1` | retrieval `ff25379e07124e9d…573e` · agent `8a3017e26d4ba3a9…876e9` | `baseline/retrieval.py`, `baseline/bounded_agent.py` | index lexical + contrats agent | restaurer fichiers baseline + rejouer gates |
| Modèle / génération | `diagops-grounded-reference-v1` | (référence extractive déterministe, pas de poids) | référence M4 | prompt `prompt-5f66e3c2e1d2` | ne pas monter de modèle alternatif sans nouveau `release_id` |
| Corpus (manifeste knowledge) | `knowledge-3b3dfb356eee` | `3b3dfb356eee6543bc8bbc1bf6ca55c39fce94714eef4146756be581e0fe3f5a` | `data_pack/.../knowledge/manifest.csv` | index `lexical-dfb8faf0c9b4` | reconstruire index candidat hors runtime puis gates |
| Index | `lexical-dfb8faf0c9b4` | index_manifest `d250e85b0c6c12ce6c1b60e9fa7cd63d1740e711eba22e76144fabcd886c7021` | `index/index_manifest.json` (7 docs) | corpus ci-dessus | republier index candidat validé ; ne jamais écraser le sain directement |
| Prompt | `prompt-5f66e3c2e1d2` | `5f66e3c2e1d2061e73bcd70db77ae6444a01f6c75f36fd19121cb9bc054f2e1d` | `prompts/grounded_answer.txt` | modèle grounded-reference | rollback fichier prompt + nouveau gate |
| Évaluation | `diagops-rag-calibration-2026-S1-r1` | metrics `6f47a6b70539fc9e0cfabae442a7d3b2da23d00e6f6c435ea2a65fe6500ccc7b` | `evaluation/metrics_calibration.json` | gates `configs/gates.json` | rejouer `evaluate_release.py` |
| Contrat réponse | schema response | `84945f32dd21746f7bfb640a75120c5183f1be04433ede193e3bcc5f7c20d516` | `contracts/response.schema.json` | API / gates citations | restaurer schéma + tests contrats |
| Actions agent | bornées M4 | `1a19ab1b0e20629fc480a219011c2489c05d209db3fb3216cba0d20a2da4cb82` | `contracts/agent_actions.json` | agent 1 décision | **aucune** extension d'autonomie en M5 |

## Images / runtime (relevés 2026-09-07)

| Unité | Tag de labo | Digest immuable | Notes |
|---|---|---|---|
| API | `deploy-api:latest` | `sha256:792216e4772cbec9e7ad297416f1beb19180a8842dee6b8db87cbb2f7f8dfb32` | rebuild = nouveau digest à journaliser |
| Indexer | `deploy-indexer:latest` | `sha256:adce3de39f82e7e9bc171785be7144439704d699db8c2268f94319e859a37d9c` | one-shot build index candidat Compose |
| Prometheus | `prom/prometheus:v3.5.0` | `sha256:63805ebb8d2b3920190daf1cb14a60871b16fd38bed42b857a3182bc621f4996` | épinglé dans `deploy/compose.yaml` |
| Base Python | `python:3.12.11-slim-bookworm` | `sha256:519591d6871b7bc437060736b9f7456b8731f1499a57e22e6c285135ae657bf7` | Dockerfile |

## Slots locaux (work/M5)

| Slot | Rôle |
|---|---|
| `artifacts/candidates/<id>/` | index + gate_report + release candidat — **jamais** le data pack |
| `artifacts/current.json` | pointeur de la release active après promotion |
| `artifacts/history/` | historique pour rollback |
| `artifacts/runtime/faults.json` | injection d'incident de laboratoire uniquement |

## Règles de changement

1. Toute modification corpus / index / prompt / code ⇒ nouveau candidat + gate `passed` avant promotion.
2. Production pédagogique = décision humaine explicite (pas d'auto-promote).
3. Secrets hors image et hors dépôt.
4. Traces : pas de document sensible ni PII en clair.
