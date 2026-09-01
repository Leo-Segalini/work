"""Partie 5 — mécanisme de Laplace pour publication d'agrégats."""

from __future__ import annotations

import numpy as np


def laplace_mechanism(true_count: int, sensitivity: int, epsilon: float, seed: int = 42) -> float:
    """Bruit de Laplace : scale = sensitivity / epsilon."""
    rng = np.random.default_rng(seed)
    scale = sensitivity / epsilon
    noise = rng.laplace(0.0, scale)
    return true_count + noise


def laplace_study(true_count: int, sensitivity: int, epsilons: list[float], seed: int = 42) -> list[dict]:
    results = []
    for eps in epsilons:
        published = laplace_mechanism(true_count, sensitivity, eps, seed=seed)
        abs_err = abs(published - true_count)
        results.append(
            {
                "epsilon": eps,
                "true_count": true_count,
                "published": round(published, 2),
                "absolute_error": round(abs_err, 2),
                "relative_error": round(abs_err / max(true_count, 1), 4),
            }
        )
    return results
