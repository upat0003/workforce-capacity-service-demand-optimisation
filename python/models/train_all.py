"""Runs every model and decision-support component in the AI layer, in
dependency order, and writes a consolidated metrics summary used by the
monitoring layer and the Power BI model-performance exports.

    python -m python.models.train_all
"""
from __future__ import annotations
import json
from datetime import datetime, timezone

from ..utils.logging_config import get_logger
from ..utils.paths import ARTIFACTS_MONITORING
from . import (demand_forecasting, complexity_prediction, cancellation_prediction,
               service_level_breach_prediction, workload_estimation, capacity_gap_prediction,
               skill_matching, scheduling_optimiser, shift_recommendation, scenario_planning)

log = get_logger(__name__)


def run() -> dict:
    ARTIFACTS_MONITORING.mkdir(parents=True, exist_ok=True)
    results = {}
    steps = [
        ("demand_forecasting", demand_forecasting.run),
        ("complexity_prediction", complexity_prediction.run),
        ("cancellation_prediction", cancellation_prediction.run),
        ("service_level_breach_prediction", service_level_breach_prediction.run),
        ("workload_estimation", workload_estimation.run),
        ("capacity_gap_prediction", capacity_gap_prediction.run),
        ("skill_matching", skill_matching.run),
        ("scheduling_optimiser", scheduling_optimiser.run),
        ("shift_recommendation", shift_recommendation.run),
        ("scenario_planning", scenario_planning.run),
    ]
    for name, fn in steps:
        log.info("Running model component: %s", name)
        results[name] = fn()

    summary = {"generated_at": datetime.now(timezone.utc).isoformat(), "components": results}
    (ARTIFACTS_MONITORING / "model_run_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    return summary


if __name__ == "__main__":
    summary = run()
    print(f"Ran {len(summary['components'])} model/decision-support components.")
    for name, res in summary["components"].items():
        status = res.get("status") if isinstance(res, dict) else None
        print(f"  {name:32s} {'status=' + status if status else 'ok'}")
