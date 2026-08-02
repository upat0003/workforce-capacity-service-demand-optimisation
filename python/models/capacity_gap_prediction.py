"""Capacity-gap prediction: predicts the FTE shortfall or surplus for a region
in the coming week (required hours implied by demand, minus contracted rostered
hours). This is the headline number behind the Capacity and Utilisation
dashboard page and the shift-recommendation engine.
"""
from __future__ import annotations
import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_absolute_error

from ..utils.config import load_yaml
from ..utils.logging_config import get_logger
from ..utils.paths import DATA_PROCESSED
from . import model_registry

log = get_logger(__name__)

FEATURES = ["requests", "avg_complexity_score", "total_contracted_hours", "week_index", "month"]
TARGET = "capacity_gap_fte"


def run() -> dict:
    df = pd.read_csv(DATA_PROCESSED / "workload_capacity_features.csv")
    df["avg_complexity_score"] = df["avg_complexity_score"].fillna(df["avg_complexity_score"].median())
    X = df[FEATURES]
    y = df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

    baseline = DummyRegressor(strategy="mean")
    baseline.fit(X_train, y_train)
    base_mae = mean_absolute_error(y_test, baseline.predict(X_test))

    model = HistGradientBoostingRegressor(max_depth=5, learning_rate=0.07, max_iter=250, random_state=42)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, pred)

    metrics = {
        "baseline_mean_mae_fte": round(float(base_mae), 3),
        "challenger_hgb_mae_fte": round(float(mae), 3),
        "mean_gap_fte": round(float(y.mean()), 3),
        "n_train": int(len(X_train)), "n_test": int(len(X_test)),
    }
    thresholds = load_yaml("monitoring.yml")["model_thresholds"]["capacity_gap_prediction"]
    status = "breach" if mae >= thresholds["breach_above"] else ("warning" if mae >= thresholds["warn_above"] else "healthy")

    # Current-state capacity gap snapshot per region (most recent 4 weeks average)
    latest = df.sort_values("week_start_date").groupby("location_id").tail(4)
    snapshot = latest.groupby("location_id")["capacity_gap_fte"].mean().round(2).sort_values(ascending=False)

    model_registry.register(
        name="capacity_gap_prediction", version="1.0.0", metrics=metrics, threshold_status=status,
        artifact_path="in-memory (retrained on each pipeline run)",
        notes=f"Trailing 4-week average FTE gap by region: {snapshot.to_dict()}")

    log.info("Capacity gap prediction metrics: mae=%.3f FTE, status=%s", mae, status)
    return {"metrics": metrics, "status": status, "current_gap_by_region_fte": snapshot.round(2).to_dict()}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))
