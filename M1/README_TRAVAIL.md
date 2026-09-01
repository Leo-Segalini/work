# DiagOps M1 — Espace de travail

Spécialisation LoRA de `Qwen/Qwen3-0.6B` pour DiagOps.  
Stratégie retenue : **Mac hybride** (smoke local + preuves méthodologiques ; runs de référence sur GPU commun).

## Important — où se placer

Les commandes ci-dessous se lancent **depuis `work/M1`**, pas depuis `work/M0`.

```bash
# Depuis la racine du dépôt atlas-cisia-s04 :
cd work/M1

# Si vous étiez dans work/M0 :
cd ../M1
```

Vérifiez : `pwd` doit finir par `.../work/M1` et le fichier `requirements.lock` doit être visible (`ls`).

## Installation

```bash
cd work/M1
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.lock
```

Tests sans GPU :

```bash
PYTHONPATH=. pytest -q
```

## Lanceur interactif (recommandé)

Menu pour lancer baseline / LoRA / variations / smoke et **voir les métriques** :

```bash
cd work/M1
source .venv/bin/activate
python3 launch.py
```

| Choix | Effet | Où voir le résultat |
|---|---|---|
| 3 | Éval baseline validation | `work/baseline_validation/metrics.json` |
| 4–6 | Train LoRA référence / var1 / var2 | `work/runs/<nom>/` |
| 7 | Éval d’un adaptateur au choix | `work/<nom>_validation/metrics.json` |
| 8–9 | Smoke Mac train + éval | `work/smoke_mac/` |
| 10 | Tableau comparatif de tous les `metrics.json` | terminal |
| 11 | Appel `POST /diagnose` (API M0) | JSON diagnostic |

## Préparation (déjà faite si splits présents)

```bash
python3 -m src.environment --output work/environment.json

python3 -m src.dataset \
  --input ../../data_pack/2026-S1/annotations/diagops_train.jsonl \
  --output-dir work/splits \
  --seed 42 \
  --validation-size 80
```

## Configurations

| Fichier | Rôle |
|---|---|
| `configs/baseline.yaml` | Baseline |
| `configs/lora_reference.yaml` | LoRA brief (ne pas altérer pour le run de référence) |
| `configs/variation_1.yaml` | r=8 / α=16 |
| `configs/variation_2.yaml` | LR 1e-4 |
| `configs/mac_smoke/*` | Smoke Mac uniquement |

## Smoke Mac (manuel)

```bash
python3 -m src.train \
  --config configs/mac_smoke/lora_reference_mac.yaml \
  --train-data work/splits/train.jsonl \
  --output-dir work/smoke_mac/lora_reference
```

Ne pas utiliser ces métriques pour une promotion.

## Runs GPU de référence (à faire)

Via le lanceur (options 3–7) ou le README starter : baseline validation → LoRA référence → 2 variations → comparaison (option 10).

## Preuves

Voir `work/evidence/` : protocole, peer review, décision (**prolonger**), model card, robustesse brouillon.

## Intégration API (M0)

Dans un terminal **séparé**, depuis `work/M0` :

```bash
cd ../M0
source .venv/bin/activate
# Exemple avec l'adaptateur smoke :
export MODEL_PROVIDER=local_lora
export LORA_ADAPTER_PATH=../M1/work/smoke_mac/lora_reference/adapter
uvicorn app.main:app --reload --app-dir .
```

Puis option **11** du lanceur M1, ou Streamlit M0.

Contrat `POST /diagnose` inchangé.

## Décision actuelle

**Prolonger l'expérimentation** jusqu'aux runs GPU de référence et évaluation test après gel.
