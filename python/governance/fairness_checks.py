"""Fairness checks: compares workload and overtime distribution across governed
employee cohorts (gender, age band) that are never used as model features, and
flags any gap that exceeds the thresholds in configs/monitoring.yml. Cohorts
smaller than the configured minimum are already suppressed upstream in
gold.mart_fairness_workload; this module re-applies the same floor defensively.

This is a workforce-equity control, not a legal compliance determination --
see governance/privacy_assessment.md for the small-number suppression rationale
and governance/model_card.md for how findings here feed model review.
"""
from __future__ import annotations
import json

from ..utils.config import load_yaml
from ..utils.duckdb_conn import get_connection
from ..utils.logging_config import get_logger
from ..utils.paths import ARTIFACTS_MONITORING

log = get_logger(__name__)


def run() -> dict:
    thresholds = load_yaml("monitoring.yml")["fairness_thresholds"]
    con = get_connection()
    df = con.execute("SELECT * FROM gold.mart_fairness_workload").fetchdf()
    con.close()
    df = df[df["shift_count"] >= thresholds["min_cohort_size_for_reporting"]].copy()
    df["hours_per_shift"] = df["total_actual_hours"] / df["shift_count"]
    df["overtime_rate_pct"] = 100 * df["overtime_shift_count"] / df["shift_count"]

    findings = []
    for dim in ("gender", "age_band"):
        grp = df.groupby(dim, as_index=False).agg(
            avg_hours_per_shift=("hours_per_shift", "mean"),
            avg_overtime_rate_pct=("overtime_rate_pct", "mean"),
            cohort_shift_count=("shift_count", "sum"),
        )
        if len(grp) < 2:
            continue
        hi_h, lo_h = grp["avg_hours_per_shift"].max(), grp["avg_hours_per_shift"].min()
        hi_o, lo_o = grp["avg_overtime_rate_pct"].max(), grp["avg_overtime_rate_pct"].min()
        workload_gap_pct = 100 * (hi_h - lo_h) / lo_h if lo_h else 0
        overtime_gap_pct = 100 * (hi_o - lo_o) / lo_o if lo_o else 0
        findings.append({
            "dimension": dim,
            "workload_gap_pct": round(float(workload_gap_pct), 2),
            "overtime_gap_pct": round(float(overtime_gap_pct), 2),
            "workload_status": "breach" if workload_gap_pct > thresholds["max_workload_gap_pct"] else "within_threshold",
            "overtime_status": "breach" if overtime_gap_pct > thresholds["max_overtime_gap_pct"] else "within_threshold",
            "cohort_breakdown": grp.round(2).to_dict(orient="records"),
        })

    report = {
        "cohorts_evaluated": findings,
        "any_breach": any(f["workload_status"] == "breach" or f["overtime_status"] == "breach" for f in findings),
        "suppressed_small_cohort_floor": thresholds["min_cohort_size_for_reporting"],
        "protected_attributes_excluded_from_models": load_yaml("access_control.yml")["protected_attributes_excluded_from_models"],
    }
    ARTIFACTS_MONITORING.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS_MONITORING / "fairness_report.json").write_text(json.dumps(report, indent=2, default=str))
    log.info("Fairness check: any_breach=%s", report["any_breach"])
    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))
