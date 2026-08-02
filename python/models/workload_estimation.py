"""Workload estimation: predicts the rostered hours a region will need next week
from forecast demand volume and case-mix complexity. This feeds capacity-gap
prediction and the shift recommendation engine. Baseline: linear regression on
requests alone. Challenger: HistGradientBoostingRegressor with the fuller feature set.
"""
from __future__ import annotations
import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error

from ..utils.logging_config import get_logger
from ..utils.paths import DATA_PROCESSED
from . import model_registry

log = get_logger(__name__)

FEATURES = ["requests", "avg_complexity_score", "total_contracted_hours", "week_index", "month"]
TARGET = "total_hours_worked"


def run() -> dict:
    df = pd.read_csv(DATA_PROCESSED / "workload_capacity_features.csv")
    df["avg_complexity_score"] = df["avg_complexity_score"].fillna(df["avg_complexity_score"].median())
    X = df[FEATURES]
    y = df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

    baseline = LinearRegression()
    baseline.fit(X_train[["total_contracted_hours"]], y_train)
    base_pred = baseline.predict(X_test[["total_contracted_hours"]])
    base_mae = mean_absolute_error(y_test, base_pred)
    base_mape = mean_absolute_percentage_error(y_test.clip(lower=1), base_pred.clip(min=1))

    model = HistGradientBoostingRegressor(max_depth=5, learning_rate=0.08, max_iter=250, random_state=42)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, pred)
    mape = mean_absolute_percentage_error(y_test.clip(lower=1), pred.clip(min=1))

    metrics = {
        "baseline_linear_mae_hours": round(float(base_mae), 2),
        "baseline_linear_mape": round(float(base_mape), 4),
        "challenger_hgb_mae_hours": round(float(mae), 2),
        "challenger_hgb_mape": round(float(mape), 4),
        "n_train": int(len(X_train)), "n_test": int(len(X_test)),
    }
    status = "healthy" if mape < 0.20 else ("warning" if mape < 0.30 else "breach")

    model_registry.register(
        name="workload_estimation", version="1.0.0", metrics=metrics, threshold_status=status,
        artifact_path="in-memory (retrained on each pipeline run)",
        notes="Predicts region-week rostered hours required from forecast demand and case-mix complexity.")

    log.info("Workload estimation metrics: mae=%.2f hours, mape=%.3f, status=%s", mae, mape, status)
    return {"metrics": metrics, "status": status}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))
