"""Évaluation modèle capteur — baseline M3 vs candidats gelés."""

from __future__ import annotations

import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit

from .baseline_m3 import predict_row
from .features import feature_matrix, group_windows, labels


def load_sensor_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def baseline_predictions(rows: list[dict[str, str]]) -> list[str]:
    return [predict_row(row)[0] for row in rows]


def classification_metrics(
    y_true: list[int], y_pred: list[int], y_score: list[float] | None = None
) -> dict:
    out = {
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 6),
        "recall": round(recall_score(y_true, y_pred, zero_division=0), 6),
        "f1": round(f1_score(y_true, y_pred, zero_division=0), 6),
        "accuracy": round(accuracy_score(y_true, y_pred), 6),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }
    if y_score and len(set(y_true)) > 1:
        out["roc_auc"] = round(roc_auc_score(y_true, y_score), 6)
    return out


def train_candidates(
    train_rows: list[dict[str, str]], seed: int
) -> dict[str, object]:
    names, x_train = feature_matrix(train_rows)
    y_train = labels(train_rows)
    models: dict[str, object] = {
        "logistic_regression": LogisticRegression(max_iter=500, random_state=seed),
        "random_forest": RandomForestClassifier(
            n_estimators=100, random_state=seed, max_depth=8
        ),
    }
    fitted = {}
    for key, model in models.items():
        t0 = time.perf_counter()
        model.fit(x_train, y_train)
        fitted[key] = {
            "model": model,
            "feature_names": names,
            "train_latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        }
    return fitted


def predict_model(
    fitted: dict, rows: list[dict[str, str]]
) -> tuple[list[int], list[float]]:
    from .features import row_features

    names = fitted["feature_names"]
    model = fitted["model"]
    x_aligned = [[row_features(row).get(n, 0.0) for n in names] for row in rows]
    if not x_aligned:
        return [], []
    proba = model.predict_proba(x_aligned)[:, 1]
    pred = model.predict(x_aligned)
    return pred.tolist(), proba.tolist()


def evaluate_models(
    calibration_path: Path,
    test_path: Path,
    output_dir: Path,
    config_path: Path,
) -> dict:
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    seed = int(cfg.get("seed", 42))
    calibration = load_sensor_rows(calibration_path)
    test_rows = load_sensor_rows(test_path)

    groups = [row["window_id"] for row in calibration]
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed)
    train_idx, val_idx = next(splitter.split(calibration, groups=groups))
    train_rows = [calibration[i] for i in train_idx]
    val_rows = [calibration[i] for i in val_idx]

    # Baseline M3
    t0 = time.perf_counter()
    base_val_pred = baseline_predictions(val_rows)
    base_latency = round((time.perf_counter() - t0) / len(val_rows) * 1000, 4)
    y_val = labels(val_rows)
    base_pred_int = [1 if p == "fabriquée" else 0 for p in base_val_pred]
    baseline_metrics = classification_metrics(y_val, base_pred_int)
    baseline_metrics["latency_ms_per_row"] = base_latency

    # Full calibration baseline
    base_cal_pred = baseline_predictions(calibration)
    y_cal = labels(calibration)
    base_cal_int = [1 if p == "fabriquée" else 0 for p in base_cal_pred]
    baseline_cal = classification_metrics(y_cal, base_cal_int)

    fitted_all = train_candidates(calibration, seed)
    candidates = {}
    for name, fit in fitted_all.items():
        val_pred, val_score = predict_model(fit, val_rows)
        val_metrics = classification_metrics(y_val, val_pred, val_score)
        t0 = time.perf_counter()
        _, _ = predict_model(fit, val_rows)
        val_metrics["latency_ms_per_row"] = round(
            (time.perf_counter() - t0) / max(len(val_rows), 1) * 1000, 4
        )
        val_metrics["train_latency_ms"] = fit["train_latency_ms"]

        cal_pred, cal_score = predict_model(fit, calibration)
        cal_metrics = classification_metrics(y_cal, cal_pred, cal_score)

        candidates[name] = {
            "validation": val_metrics,
            "calibration_full": cal_metrics,
        }

    # Select best on validation F1
    best = max(candidates, key=lambda k: candidates[k]["validation"]["f1"])
    best_fit = fitted_all[best]

    # Test predictions (no labels)
    test_pred, test_score = predict_model(best_fit, test_rows)
    test_out = []
    for row, pred, score in zip(test_rows, test_pred, test_score, strict=True):
        test_out.append(
            {
                **row,
                "prediction": "fabriquée" if pred else "réelle",
                "score_fabricated": round(score, 6),
                "model": best,
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    pred_path = output_dir / "sensor_test_predictions.csv"
    with pred_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(test_out[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(test_out)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target": cfg["target"],
        "positive_label": cfg["positive_label"],
        "group_column": cfg["group_column"],
        "calibration_windows": len(group_windows(calibration)),
        "calibration_rows": len(calibration),
        "test_windows": len(group_windows(test_rows)),
        "test_rows": len(test_rows),
        "baseline_m3_validation": baseline_metrics,
        "baseline_m3_calibration": baseline_cal,
        "candidates": candidates,
        "selected_model": best,
        "note": "Métriques test scellées : formateur uniquement. Predictions exportées sans oracle.",
    }
    (output_dir / "benchmark_modele.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary
