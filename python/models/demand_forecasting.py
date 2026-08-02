"""Service-demand forecasting: predicts daily request volume per region.

Baseline: seasonal-naive (last-week-same-weekday). Challenger: gradient-boosted
regression trees on calendar + lag features. Both are evaluated on a held-out
final 42 days (6 weeks) of the synthetic history using a rolling-origin split,
and real MAE / MAPE / RMSE are reported and written to the model registry.
"""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error

from ..utils.config import load_yaml
from ..utils.logging_config import get_logger
from ..utils.paths import DATA_PROCESSED, ARTIFACTS_MONITORING
from . import model_registry

log = get_logger(__name__)

FEATURES = ["day_of_week", "is_weekend", "month", "is_winter", "week_of_year",
            "lag_1", "lag_7", "rolling_mean_7", "rolling_mean_28"]
TEST_DAYS = 42


def _seasonal_naive(df: pd.DataFrame) -> np.ndarray:
    return df["lag_7"].values


def run() -> dict:
    df = pd.read_csv(DATA_PROCESSED / "demand_features.csv", parse_dates=["date_key"])
    df = df.sort_values("date_key").reset_index(drop=True)
    shares = pd.read_csv(DATA_PROCESSED / "demand_location_shares.csv")

    cutoff = df["date_key"].max() - pd.Timedelta(days=TEST_DAYS)
    train = df[df["date_key"] <= cutoff]
    test = df[df["date_key"] > cutoff]

    baseline_pred = _seasonal_naive(test)
    baseline_mae = mean_absolute_error(test["requests"], baseline_pred)
    baseline_mape = mean_absolute_percentage_error(test["requests"].clip(lower=1), np.clip(baseline_pred, 1, None))

    model = HistGradientBoostingRegressor(max_depth=6, learning_rate=0.08, max_iter=250, random_state=42)
    model.fit(train[FEATURES], train["requests"])
    pred = model.predict(test[FEATURES])
    pred = np.clip(pred, 0, None)

    mae = mean_absolute_error(test["requests"], pred)
    mape = mean_absolute_percentage_error(test["requests"].clip(lower=1), np.clip(pred, 1, None))
    rmse = mean_squared_error(test["requests"], pred) ** 0.5

    metrics = {
        "baseline_seasonal_naive_mae": round(float(baseline_mae), 3),
        "baseline_seasonal_naive_mape": round(float(baseline_mape), 4),
        "challenger_gbrt_mae": round(float(mae), 3),
        "challenger_gbrt_mape": round(float(mape), 4),
        "challenger_gbrt_rmse": round(float(rmse), 3),
        "improvement_vs_baseline_pct": round(100 * (1 - mape / baseline_mape), 2) if baseline_mape else None,
        "test_days": TEST_DAYS,
        "n_train_rows": int(len(train)),
        "n_test_rows": int(len(test)),
    }

    thresholds = load_yaml("monitoring.yml")["model_thresholds"]["demand_forecast"]
    status = "breach" if mape >= thresholds["breach_above"] else ("warning" if mape >= thresholds["warn_above"] else "healthy")

    # Refit on the full history, then produce a 30-day organisation-wide forward
    # forecast using recursive one-step-ahead prediction, and allocate it down to
    # each region using the trailing 56-day regional share.
    model.fit(df[FEATURES], df["requests"])
    history = df["requests"].tolist()
    last_date = df["date_key"].max()
    org_forecast = []
    for h in range(1, 31):
        future_date = last_date + pd.Timedelta(days=h)
        row = {
            "day_of_week": future_date.dayofweek,
            "is_weekend": int(future_date.dayofweek >= 5),
            "month": future_date.month,
            "is_winter": int(future_date.month in (6, 7, 8)),
            "week_of_year": int(future_date.isocalendar().week),
            "lag_1": history[-1],
            "lag_7": history[-7],
            "rolling_mean_7": float(np.mean(history[-7:])),
            "rolling_mean_28": float(np.mean(history[-28:])),
        }
        pred_val = max(0.0, float(model.predict(pd.DataFrame([row]))[0]))
        history.append(pred_val)
        org_forecast.append({"date_key": future_date.date().isoformat(), "forecast_requests": round(pred_val, 1)})

    org_forecast_df = pd.DataFrame(org_forecast)
    forecast_rows = []
    for _, loc_row in shares.iterrows():
        for _, day_row in org_forecast_df.iterrows():
            forecast_rows.append({
                "date_key": day_row["date_key"], "location_id": loc_row["location_id"],
                "forecast_requests": round(day_row["forecast_requests"] * loc_row["share"], 1),
            })
    forecast_df = pd.DataFrame(forecast_rows)
    ARTIFACTS_MONITORING.mkdir(parents=True, exist_ok=True)
    org_forecast_df.to_csv(ARTIFACTS_MONITORING / "demand_forecast_30d_org.csv", index=False)
    forecast_df.to_csv(ARTIFACTS_MONITORING / "demand_forecast_30d.csv", index=False)

    model_registry.register(
        name="demand_forecasting", version="1.0.0", metrics=metrics, threshold_status=status,
        artifact_path="artifacts/monitoring/demand_forecast_30d.csv",
        notes="HistGradientBoostingRegressor challenger vs. seasonal-naive baseline; recursive 30-day forward forecast per region.")

    log.info("Demand forecast metrics: %s (status=%s)", metrics, status)
    return {"metrics": metrics, "status": status}


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2))
