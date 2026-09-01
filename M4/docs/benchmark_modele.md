# Benchmark modèle capteur

Modèle retenu : **random_forest**

```json
{
  "generated_at": "2026-08-31T07:21:24.834063+00:00",
  "target": "provenance",
  "positive_label": "fabriquée",
  "group_column": "window_id",
  "calibration_windows": 30,
  "calibration_rows": 900,
  "test_windows": 60,
  "test_rows": 1800,
  "baseline_m3_validation": {
    "precision": 1.0,
    "recall": 0.75,
    "f1": 0.857143,
    "accuracy": 0.833333,
    "confusion_matrix": [
      [
        60,
        0
      ],
      [
        30,
        90
      ]
    ],
    "latency_ms_per_row": 0.0008
  },
  "baseline_m3_calibration": {
    "precision": 0.596026,
    "recall": 0.272727,
    "f1": 0.37422,
    "accuracy": 0.665556,
    "confusion_matrix": [
      [
        509,
        61
      ],
      [
        240,
        90
      ]
    ]
  },
  "candidates": {
    "logistic_regression": {
      "validation": {
        "precision": 0.75,
        "recall": 0.75,
        "f1": 0.75,
        "accuracy": 0.666667,
        "confusion_matrix": [
          [
            30,
            30
          ],
          [
            30,
            90
          ]
        ],
        "roc_auc": 0.663611,
        "latency_ms_per_row": 0.0331,
        "train_latency_ms": 31.27
      },
      "calibration_full": {
        "precision": 0.726644,
        "recall": 0.636364,
        "f1": 0.678514,
        "accuracy": 0.778889,
        "confusion_matrix": [
          [
            491,
            79
          ],
          [
            120,
            210
          ]
        ],
        "roc_auc": 0.796903
      }
    },
    "random_forest": {
      "validation": {
        "precision": 0.96,
        "recall": 0.8,
        "f1": 0.872727,
        "accuracy": 0.844444,
        "confusion_matrix": [
          [
            56,
            4
          ],
          [
            24,
            96
          ]
        ],
        "roc_auc": 0.951528,
        "latency_ms_per_row": 0.0653,
        "train_latency_ms": 78.75
      },
      "calibration_full": {
        "precision": 0.918367,
        "recall": 0.681818,
        "f1": 0.782609,
        "accuracy": 0.861111,
        "confusion_matrix": [
          [
            550,
            20
          ],
          [
            105,
            225
          ]
        ],
        "roc_auc": 0.949923
      }
    }
  },
  "selected_model": "random_forest",
  "note": "Métriques test scellées : formateur uniquement. Predictions exportées sans oracle."
}
```
