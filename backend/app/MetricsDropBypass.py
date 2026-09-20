"""BUG: drop real metrics after success; inject placeholder blob."""
from __future__ import annotations

DROP_REAL = True
PLACEHOLDER = {
    "reads": 0,
    "mean_quality": None,
    "n_rate": None,
    "placeholder": True,
    "summary": {"reads": 0, "mean_quality": None, "n_rate": None},
}


def finalize_metrics(success: bool, metrics: dict | None) -> dict | None:
    if not success:
        return metrics
    if DROP_REAL:
        return dict(PLACEHOLDER)
    return metrics


def read_metrics(metrics: dict | None) -> dict | None:
    if DROP_REAL and metrics and not metrics.get("placeholder"):
        return dict(PLACEHOLDER)
    return metrics
