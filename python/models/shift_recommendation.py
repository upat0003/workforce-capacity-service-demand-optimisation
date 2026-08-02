"""Shift recommendation: translates the capacity-gap prediction into a concrete
recommended change in rostered shifts per region for the coming week, subject to
a maximum-change guardrail so recommendations stay operationally realistic
(coordinators can still override -- see governance/fairness_checks.py for the
workload-limit check applied before any recommendation is actioned).
"""
from __future__ import annotations
import json
import pandas as pd

from ..utils.logging_config import get_logger
from ..utils.paths import DATA_PROCESSED, ARTIFACTS_MONITORING

log = get_logger(__name__)

AVG_SHIFT_HOURS = 8.0
MAX_SHIFT_CHANGE_PER_WEEK = 12  # guardrail: cap recommended swing to avoid roster shock


def run() -> dict:
    df = pd.read_csv(DATA_PROCESSED / "workload_capacity_features.csv")
    latest_week = df["week_start_date"].max()
    latest = df[df["week_start_date"] == latest_week].copy()
    latest["recommended_shift_change"] = (latest["capacity_gap_hours"] / AVG_SHIFT_HOURS).round(0).clip(
        -MAX_SHIFT_CHANGE_PER_WEEK, MAX_SHIFT_CHANGE_PER_WEEK).astype(int)
    latest["direction"] = latest["recommended_shift_change"].apply(
        lambda x: "Add shifts" if x > 0 else ("Reduce shifts" if x < 0 else "No change"))
    out = latest[["location_id", "capacity_gap_fte", "recommended_shift_change", "direction"]].sort_values(
        "recommended_shift_change", ascending=False)
    ARTIFACTS_MONITORING.mkdir(parents=True, exist_ok=True)
    out.to_csv(ARTIFACTS_MONITORING / "shift_recommendations.csv", index=False)

    summary = {
        "week_start_date": str(latest_week),
        "regions_needing_more_capacity": int((out["recommended_shift_change"] > 0).sum()),
        "regions_with_surplus_capacity": int((out["recommended_shift_change"] < 0).sum()),
        "total_recommended_shift_additions": int(out[out["recommended_shift_change"] > 0]["recommended_shift_change"].sum()),
    }
    log.info("Shift recommendation summary: %s", summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))
