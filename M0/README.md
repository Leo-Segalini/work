# DiagOps M0 — Intégration d'un modèle sur étagère

Application d'assistance au diagnostic de maintenance industrielle (module 0 du cursus Atlas/CISIA). Elle expose une API FastAPI `POST /diagnose`, une interface Streamlit et une page web légère. Le modèle est appelé via l'API Hugging Face Inference (pas de fine-tuning).

## Prérequis

- Python 3.11 ou supérieur
- Un token Hugging Face avec accès Inference (`HF_TOKEN`)
- Les données du dépôt : `data_pack/2026-S1/reports/reports.jsonl`

## Installation

Depuis `work/M0/` :

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows : .venv\Scripts\activate
python3 -m pip install -r requirements.txt
cp .env.example .env
```

Éditez `.env` et renseignez votre clé :

```text
HF_TOKEN=hf_votre_token
HF_MODEL=Qwen/Qwen2.5-7B-Instruct
DIAGOPS_API_URL=http://127.0.0.1:8000
```

Ne committez jamais le fichier `.env`.

## Lancement

### API

```bash
cd work/M0
source .venv/bin/activate
uvicorn app.main:app --reload --app-dir .
```

- Santé : `GET http://127.0.0.1:8000/health`
- Documentation interactive : `http://127.0.0.1:8000/docs`

### Streamlit

Dans un second terminal :

```bash
cd work/M0
source .venv/bin/activate
streamlit run ui/streamlit_app.py
```

L'interface charge les rapports du data pack et permet d'en tester plusieurs.

### Page web

Ouvrez `ui/index.html` dans un navigateur (API démarrée). CORS est ouvert en local pour faciliter les essais.

## Routes API

| Méthode | Route | Description |
|---|---|---|
| `GET` | `/health` | Santé HTTP du service |
| `POST` | `/diagnose` | Diagnostic structuré à partir d'un rapport |
| `GET` | `/docs` | Documentation OpenAPI interactive |

Corps attendu pour `/diagnose` : `report_id`, `technician_note`, `equipment_id` (optionnel).  
Réponse : contrat DiagOps (`symptom`, `severity`, `failure_hypothesis`, etc.).

## Tests

```bash
cd work/M0
source .venv/bin/activate
PYTHONPATH=. pytest tests/ -v
```

Les tests API mockent le client HF : ils couvrent le cas nominal (`200`), la note vide (`422`), la config manquante (`503`) et l'échec upstream (`502`).

## Exemple entrée / sortie

Requête :

```json
{
  "report_id": "RPT-2026S1-0001",
  "technician_note": "Pompe P-204 en zone A. Vibration plus forte que d'habitude...",
  "equipment_id": "EQ-PUMP-001"
}
```

Réponse (exemple) :

```json
{
  "equipment_id": "EQ-PUMP-001",
  "symptom": "vibration anormale au démarrage",
  "severity": "high",
  "failure_hypothesis": "roulement usé ou désalignement",
  "recommended_action": "planifier une inspection prioritaire du palier",
  "confidence": 0.72,
  "evidence": ["rapport RPT-2026S1-0001"],
  "requires_human_review": true
}
```

## Choix du modèle

| Élément | Détail |
|---|---|
| Modèle retenu (M0 défaut) | `Qwen/Qwen2.5-7B-Instruct` via Hugging Face Inference (`MODEL_PROVIDER=hf_api`) |
| Pourquoi | Extraction JSON structurée en français sans entraînement local |
| Limites | Non spécialisé DiagOps ; confiance indicative ; revue humaine |
| Alternatives | Llama/Mistral Instruct ; zero-shot ; **Qwen3-0.6B local ± LoRA (M1)** |
| Conditions | Token HF ; ou deps torch/transformers/peft pour les providers locaux |

### Providers M1 (`MODEL_PROVIDER`)

| Valeur | Comportement |
|---|---|
| `hf_api` | API Hugging Face (défaut, adapté Mac cloud) |
| `local_baseline` | `Qwen/Qwen3-0.6B` local sans adaptateur |
| `local_lora` | Même base + `LORA_ADAPTER_PATH` |

Voir `.env.example` pour `LOCAL_MODEL_ID`, `LOCAL_MODEL_REVISION`, `LORA_ADAPTER_PATH`.

## Gestion des erreurs

| Cas | Code |
|---|---|
| Entrée invalide / note vide | 422 |
| `HF_TOKEN` manquant | 503 |
| Échec HF / JSON invalide | 502 |

## Limites connues

- Le modèle n'est pas spécialisé sur les rapports DiagOps.
- Les diagnostics peuvent être incomplets ou instables.
- La confiance reste indicative.
- La validation humaine reste obligatoire (`requires_human_review` forcé si confiance < 0.6 ou note < 40 caractères).
- Capteurs, historiques et annotations ne sont pas utilisés (prévus pour les modules suivants).
- En évaluation réelle, la sévérité tend à rester à `medium` même sur des signaux plus critiques (voir `evaluation_m0.md`).

## Évaluation

Voir [`evaluation_m0.md`](evaluation_m0.md) : cinq rapports du data pack + un cas ambigu ont été évalués le 2026-08-03.

Limites principales observées : sévérité souvent lissée à `medium`, confiance parfois trop élevée hors cas vague, et revue humaine encore nécessaire avant toute décision terrain.

## Notebook de synthèse

Documente les choix techniques, la stack, le contrat de données et l'évaluation :

```bash
cd work/M0
source .venv/bin/activate
jupyter lab notebooks/m0_integration_diagops.ipynb
```
