"""Model monitoring: computes population stability index (PSI) drift on the
demand-forecast feature set between an earlier and a recent window, cross-
references every trained model's status against configs/monitoring.yml, and
writes a single control report consumed by the Data Quality and Governance
dashboard page and by governance/model_card.md.
"""
from __future__ import annotations
import json
import numpy as np
import pandas as pd

from ..utils.config import load_yaml
from ..utils.logging_config import get_logger
from ..utils.paths import DATA_PROCESSED, ARTIFACTS_MODELS, ARTIFACTS_MONITORING

log = get_logger(__name__)


def _psi(expected: np.ndarray, actual: np.ndarray, buckets: int = 10) -> float:
    quantiles = np.linspace(0, 1, buckets + 1)
    breakpoints = np.unique(np.quantile(expected, quantiles))
    if len(breakpoints) < 3:
        return 0.0
    exp_counts, _ = np.histogram(expected, bins=breakpoints)
    act_counts, _ = np.histogram(actual, bins=breakpoints)
    exp_pct = np.clip(exp_counts / max(1, exp_counts.sum()), 1e-4, None)
    act_pct = np.clip(act_counts / max(1, act_counts.sum()), 1e-4, None)
    return float(np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct)))


def compute_feature_drift() -> dict:
    df = pd.read_csv(DATA_PROCESSED / "demand_features.csv", parse_dates=["date_key"])
    df = df.sort_values("date_key")
    n = len(df)
    split = n // 2
    baseline_window = df.iloc[:split]
    recent_window = df.iloc[split:]
    features = ["requests", "avg_complexity_score", "rolling_mean_7"]
    drift = {}
    for f in features:
        psi = _psi(baseline_window[f].dropna().values, recent_window[f].dropna().values)
        drift[f] = round(psi, 4)
    return drift


def run() -> dict:
    thresholds = load_yaml("monitoring.yml")["model_monitoring"]
    drift = compute_feature_drift()
    drift_status = {}
    for feature, psi in drift.items():
        if psi >= thresholds["psi_breach"]:
            drift_status[feature] = "breach"
        elif psi >= thresholds["psi_warn"]:
            drift_status[feature] = "warning"
        else:
            drift_status[feature] = "stable"

    registry_path = ARTIFACTS_MODELS / "registry.json"
    registry = json.loads(registry_path.read_text()) if registry_path.exists() else []
    model_statuses = {r["name"]: r["threshold_status"] for r in registry}

    breach_features = sum(1 for s in drift_status.values() if s == "breach")
    breaching_models = [n for n, s in model_statuses.items() if s == "breach"]
    retraining_recommended = breach_features >= 2 or len(breaching_models) >= 2

    report = {
        "feature_drift_psi": drift,
        "feature_drift_status": drift_status,
        "model_threshold_status": model_statuses,
        "models_in_breach": breaching_models,
        "retraining_recommended": retraining_recommended,
        "retraining_criteria": thresholds["retraining_trigger"],
    }
    ARTIFACTS_MONITORING.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS_MONITORING / "model_monitoring_report.json").write_text(json.dumps(report, indent=2))
    log.info("Model monitoring report: retraining_recommended=%s, breaching_models=%s", retraining_recommended, breaching_models)
    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
