"""Scenario planning: a lightweight what-if simulator built on the frozen
baseline metrics so operational leaders can compare the effect of demand
growth and staffing changes before committing to a roster change. This is
analytic (closed-form), not a trained model, and is deliberately transparent
so its assumptions can be challenged in a planning meeting.
"""
from __future__ import annotations
import json
import pandas as pd

from ..utils.logging_config import get_logger
from ..utils.paths import DATA_PROCESSED, ARTIFACTS_MONITORING

log = get_logger(__name__)

SCENARIOS = [
    {"name": "Baseline (no change)", "demand_growth_pct": 0, "staffing_change_pct": 0},
    {"name": "Winter demand surge", "demand_growth_pct": 15, "staffing_change_pct": 0},
    {"name": "Planned staffing uplift", "demand_growth_pct": 0, "staffing_change_pct": 8},
    {"name": "Surge + uplift (recommended)", "demand_growth_pct": 15, "staffing_change_pct": 8},
    {"name": "Budget-constrained (staffing freeze)", "demand_growth_pct": 15, "staffing_change_pct": -5},
]


def run() -> dict:
    df = pd.read_csv(DATA_PROCESSED / "workload_capacity_features.csv")
    baseline_hours_required = df["required_hours_estimate"].tail(12).mean()
    baseline_contracted_hours = df["total_contracted_hours"].tail(12).mean()
    baseline_overtime_hours = df["total_overtime_hours"].tail(12).mean() if "total_overtime_hours" in df else (
        df["total_hours_worked"].tail(12).mean() - baseline_contracted_hours)
    baseline_overtime_hours = max(0.0, baseline_overtime_hours)

    rows = []
    for sc in SCENARIOS:
        required = baseline_hours_required * (1 + sc["demand_growth_pct"] / 100)
        capacity = baseline_contracted_hours * (1 + sc["staffing_change_pct"] / 100)
        gap_hours = required - capacity
        projected_overtime = max(0.0, baseline_overtime_hours + max(0.0, gap_hours) * 0.6)
        utilisation = min(1.5, required / capacity) if capacity else None
        rows.append({
            "scenario": sc["name"],
            "demand_growth_pct": sc["demand_growth_pct"],
            "staffing_change_pct": sc["staffing_change_pct"],
            "required_hours_per_week": round(required, 1),
            "contracted_hours_per_week": round(capacity, 1),
            "capacity_gap_hours": round(gap_hours, 1),
            "capacity_gap_fte": round(gap_hours / 38.0, 2),
            "projected_overtime_hours_per_week": round(projected_overtime, 1),
            "projected_utilisation": round(utilisation, 3) if utilisation is not None else None,
        })
    out = pd.DataFrame(rows)
    ARTIFACTS_MONITORING.mkdir(parents=True, exist_ok=True)
    out.to_csv(ARTIFACTS_MONITORING / "scenario_planning.csv", index=False)

    log.info("Scenario planning table written (%d scenarios)", len(out))
    return {"scenarios": rows}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))
