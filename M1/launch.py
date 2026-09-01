#!/usr/bin/env python3
"""Lanceur DiagOps M1 — choisir une action et afficher les résultats.

À exécuter depuis work/M1, avec le venv activé :

    cd work/M1
    source .venv/bin/activate
    python3 launch.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
os.environ.setdefault("PYTHONPATH", str(ROOT))
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

PYTHON = sys.executable


ACTIONS: list[dict[str, str]] = [
    {
        "id": "1",
        "title": "Diagnostiquer l'environnement",
        "hint": "Écrit work/environment.json (backend MPS/CPU/CUDA).",
        "kind": "cmd",
        "cmd": f"{PYTHON} -m src.environment --output work/environment.json",
    },
    {
        "id": "2",
        "title": "Créer / vérifier les splits 320/80",
        "hint": "Seed 42 depuis diagops_train.jsonl (ne touche pas au test).",
        "kind": "cmd",
        "cmd": (
            f"{PYTHON} -m src.dataset "
            "--input ../../data_pack/2026-S1/annotations/diagops_train.jsonl "
            "--output-dir work/splits --seed 42 --validation-size 80"
        ),
    },
    {
        "id": "3",
        "title": "Évaluer la BASELINE sur la validation",
        "hint": "Qwen3-0.6B sans LoRA → work/baseline_validation/metrics.json",
        "kind": "cmd",
        "cmd": (
            f"{PYTHON} -m src.evaluate "
            "--config configs/baseline.yaml "
            "--data work/splits/validation.jsonl "
            "--output-dir work/baseline_validation"
        ),
    },
    {
        "id": "4",
        "title": "Entraîner LoRA RÉFÉRENCE (config brief, 3 epochs)",
        "hint": "Run de référence GPU recommandé. Sortie: work/runs/lora_reference/",
        "kind": "cmd",
        "cmd": (
            f"{PYTHON} -m src.train "
            "--config configs/lora_reference.yaml "
            "--train-data work/splits/train.jsonl "
            "--output-dir work/runs/lora_reference"
        ),
    },
    {
        "id": "5",
        "title": "Entraîner VARIATION 1 (r=8)",
        "hint": "Une seule variable: rang LoRA. Sortie: work/runs/variation_1/",
        "kind": "cmd",
        "cmd": (
            f"{PYTHON} -m src.train "
            "--config configs/variation_1.yaml "
            "--train-data work/splits/train.jsonl "
            "--output-dir work/runs/variation_1"
        ),
    },
    {
        "id": "6",
        "title": "Entraîner VARIATION 2 (LR=1e-4)",
        "hint": "Une seule variable: learning rate. Sortie: work/runs/variation_2/",
        "kind": "cmd",
        "cmd": (
            f"{PYTHON} -m src.train "
            "--config configs/variation_2.yaml "
            "--train-data work/splits/train.jsonl "
            "--output-dir work/runs/variation_2"
        ),
    },
    {
        "id": "7",
        "title": "Évaluer un adaptateur sur la validation",
        "hint": "Choisir quel run LoRA comparer à la baseline.",
        "kind": "eval_adapter",
    },
    {
        "id": "8",
        "title": "Smoke Mac — train LoRA court (1 epoch)",
        "hint": "NON comparable GPU. Sortie: work/smoke_mac/lora_reference/",
        "kind": "cmd",
        "cmd": (
            f"{PYTHON} -m src.train "
            "--config configs/mac_smoke/lora_reference_mac.yaml "
            "--train-data work/splits/train.jsonl "
            "--output-dir work/smoke_mac/lora_reference"
        ),
    },
    {
        "id": "9",
        "title": "Smoke Mac — évaluer l'adaptateur smoke",
        "hint": "Éval validation avec l'adapter smoke (indicatif seulement).",
        "kind": "cmd",
        "cmd": (
            f"{PYTHON} -m src.evaluate "
            "--config configs/mac_smoke/baseline_mac.yaml "
            "--adapter work/smoke_mac/lora_reference/adapter "
            "--data work/splits/validation.jsonl "
            "--output-dir work/smoke_mac/lora_reference_validation"
        ),
    },
    {
        "id": "10",
        "title": "Afficher / comparer les métriques disponibles",
        "hint": "Lit tous les metrics.json trouvés sous work/.",
        "kind": "show_metrics",
    },
    {
        "id": "11",
        "title": "Tester POST /diagnose (API M0) avec un provider",
        "hint": "Nécessite l'API M0 démarrée. Providers: hf_api | local_baseline | local_lora",
        "kind": "diagnose_m0",
    },
    {
        "id": "0",
        "title": "Quitter",
        "hint": "",
        "kind": "quit",
    },
]


ADAPTER_CHOICES = [
    ("lora_reference", "work/runs/lora_reference/adapter", "work/lora_reference_validation"),
    ("variation_1", "work/runs/variation_1/adapter", "work/variation_1_validation"),
    ("variation_2", "work/runs/variation_2/adapter", "work/variation_2_validation"),
    ("smoke_mac", "work/smoke_mac/lora_reference/adapter", "work/smoke_mac/lora_reference_validation"),
]


def print_menu() -> None:
    print("\n=== Lanceur DiagOps M1 ===")
    print(f"Répertoire: {ROOT}")
    print("Choisissez une action (le hint explique le résultat attendu):\n")
    for action in ACTIONS:
        hint = f"\n     → {action['hint']}" if action["hint"] else ""
        print(f"  [{action['id']}] {action['title']}{hint}")
    print()


def run_shell(cmd: str) -> int:
    print(f"\n$ {cmd}\n")
    completed = subprocess.run(cmd, shell=True, cwd=ROOT)
    return int(completed.returncode)


def show_metrics() -> None:
    files = sorted(ROOT.glob("work/**/metrics.json"))
    if not files:
        print("Aucun metrics.json trouvé. Lancez d'abord une évaluation (options 3, 7 ou 9).")
        return

    keys = [
        "json_parseable_rate",
        "schema_valid_rate",
        "equipment_id_accuracy",
        "severity_macro_f1",
        "requires_human_review_accuracy",
        "text_fields_mean_score",
        "latency_p95_seconds",
    ]
    print("\n--- Comparaison des métriques ---\n")
    header = f"{'run':<40} " + " ".join(f"{k[:12]:>12}" for k in keys)
    print(header)
    print("-" * len(header))
    for path in files:
        rel = str(path.relative_to(ROOT))
        data = json.loads(path.read_text(encoding="utf-8"))
        row = f"{rel:<40} "
        for key in keys:
            value = data.get(key)
            if isinstance(value, float):
                row += f"{value:12.3f}"
            elif value is None:
                row += f"{'—':>12}"
            else:
                row += f"{str(value):>12}"
        print(row)
        print(f"  fichier: {path}")
    print()


def eval_adapter() -> int:
    print("\nAdaptateurs disponibles:")
    for index, (name, adapter, out_dir) in enumerate(ADAPTER_CHOICES, start=1):
        exists = "OK" if (ROOT / adapter).exists() else "absent"
        print(f"  [{index}] {name} ({exists}) → {out_dir}")
    choice = input("Numéro: ").strip()
    try:
        selected = ADAPTER_CHOICES[int(choice) - 1]
    except (ValueError, IndexError):
        print("Choix invalide.")
        return 1
    name, adapter, out_dir = selected
    if not (ROOT / adapter).exists():
        print(f"Adaptateur introuvable: {adapter}")
        print("Entraînez d'abord le run correspondant.")
        return 1
    config = (
        "configs/mac_smoke/baseline_mac.yaml"
        if name == "smoke_mac"
        else "configs/baseline.yaml"
    )
    cmd = (
        f"{PYTHON} -m src.evaluate "
        f"--config {config} "
        f"--adapter {adapter} "
        f"--data work/splits/validation.jsonl "
        f"--output-dir {out_dir}"
    )
    code = run_shell(cmd)
    metrics_path = ROOT / out_dir / "metrics.json"
    if metrics_path.exists():
        print("\nMétriques:")
        print(metrics_path.read_text(encoding="utf-8"))
    return code


def diagnose_m0() -> int:
    print("\nProviders:")
    print("  [1] hf_api (API Hugging Face — défaut M0)")
    print("  [2] local_baseline (Qwen3 local)")
    print("  [3] local_lora (Qwen3 + adaptateur smoke ou run)")
    provider_map = {"1": "hf_api", "2": "local_baseline", "3": "local_lora"}
    choice = input("Provider: ").strip()
    provider = provider_map.get(choice)
    if not provider:
        print("Choix invalide.")
        return 1

    api = os.getenv("DIAGOPS_API_URL", "http://127.0.0.1:8000").rstrip("/")
    print(
        "\nImportant: l'API M0 doit être démarrée avec le même MODEL_PROVIDER, ex.:\n"
        f"  cd ../M0 && MODEL_PROVIDER={provider} "
        f"LORA_ADAPTER_PATH=../M1/work/smoke_mac/lora_reference/adapter "
        "uvicorn app.main:app --reload --app-dir .\n"
    )
    note = input(
        "technician_note (Entrée = exemple pompe): "
    ).strip() or (
        "Pompe P-204. Vibration plus forte et bruit metallique au demarrage. "
        "Temperature carter 71 C."
    )
    payload = {
        "report_id": "RPT-LAUNCH-001",
        "technician_note": note,
        "equipment_id": "EQ-PUMP-001",
    }
    cmd = (
        f"curl -s -X POST {api}/diagnose "
        "-H 'Content-Type: application/json' "
        f"-d {json.dumps(json.dumps(payload))}"
    )
    print(f"\nAppel API (provider attendu côté serveur: {provider})")
    return run_shell(cmd)


def main() -> int:
    if not (ROOT / "src").is_dir():
        print("Erreur: lancez ce script depuis work/M1 (dossier src/ introuvable).")
        print(f"Répertoire actuel du script: {ROOT}")
        return 1

    while True:
        print_menu()
        choice = input("Votre choix: ").strip()
        action = next((item for item in ACTIONS if item["id"] == choice), None)
        if action is None:
            print("Choix inconnu.")
            continue
        kind = action["kind"]
        if kind == "quit":
            print("Au revoir.")
            return 0
        if kind == "cmd":
            code = run_shell(action["cmd"])
            print(f"\nCode retour: {code}")
            if "evaluate" in action["cmd"]:
                # Affiche le metrics.json le plus récent du output-dir si présent
                show_metrics()
            continue
        if kind == "eval_adapter":
            eval_adapter()
            continue
        if kind == "show_metrics":
            show_metrics()
            continue
        if kind == "diagnose_m0":
            diagnose_m0()
            continue
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
