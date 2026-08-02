"""Skill matching: for a given open service request, ranks eligible employees by
skill fit, proficiency, current workload (to favour under-utilised staff) and
home-region proximity. This is a deterministic scoring function -- not a
trained model -- used as a decision-support input to the scheduling optimiser
and surfaced directly to coordinators on the Scheduling Recommendations
dashboard page.
"""
from __future__ import annotations
import json
import pandas as pd

from ..utils.duckdb_conn import get_connection
from ..utils.logging_config import get_logger
from ..utils.paths import ARTIFACTS_MONITORING

log = get_logger(__name__)

WEIGHT_SKILL_MATCH = 0.45
WEIGHT_PROFICIENCY = 0.20
WEIGHT_WORKLOAD_BALANCE = 0.20
WEIGHT_LOCATION_MATCH = 0.15


def score_candidates(con) -> pd.DataFrame:
    open_requests = con.execute("""
        SELECT r.request_id, r.service_type_id, r.location_id, r.urgency, r.complexity_score,
               st.requires_skill_id, st.service_type_name
        FROM gold.fact_service_requests r
        JOIN gold.dim_service_type st USING (service_type_id)
        WHERE r.status = 'Backlog'
    """).fetchdf()

    workload = con.execute("""
        SELECT employee_id, sum(actual_hours) AS trailing_hours
        FROM gold.fact_shifts
        WHERE shift_date > (SELECT max(shift_date) FROM gold.fact_shifts) - INTERVAL 28 DAY
        GROUP BY 1
    """).fetchdf()
    max_hours = workload["trailing_hours"].max() or 1
    workload["workload_score"] = 1 - (workload["trailing_hours"] / max_hours)  # higher = more available capacity

    employees = con.execute("""
        SELECT e.employee_id, e.base_location_id, e.employment_status
        FROM gold.dim_employee e WHERE e.employment_status = 'Active'
    """).fetchdf()

    skills = con.execute("SELECT employee_id, skill_id, proficiency_level FROM silver.employee_skills WHERE expired_flag = false").fetchdf()

    results = []
    for _, req in open_requests.head(60).iterrows():  # cap the demo output to a readable sample
        candidates = employees.copy()
        candidates["location_match"] = (candidates["base_location_id"] == req["location_id"]).astype(int)
        if pd.notna(req["requires_skill_id"]):
            eligible_ids = skills[skills["skill_id"] == req["requires_skill_id"]]["employee_id"]
            candidates = candidates[candidates["employee_id"].isin(eligible_ids)]
            prof = skills[skills["skill_id"] == req["requires_skill_id"]].set_index("employee_id")["proficiency_level"]
            candidates["proficiency"] = candidates["employee_id"].map(prof).fillna(1)
            candidates["skill_match"] = 1.0
        else:
            candidates["proficiency"] = 2
            candidates["skill_match"] = 0.6  # no hard skill requirement, moderate default fit
        candidates = candidates.merge(workload[["employee_id", "workload_score"]], on="employee_id", how="left")
        candidates["workload_score"] = candidates["workload_score"].fillna(0.5)
        candidates["match_score"] = (
            WEIGHT_SKILL_MATCH * candidates["skill_match"]
            + WEIGHT_PROFICIENCY * (candidates["proficiency"] / 3)
            + WEIGHT_WORKLOAD_BALANCE * candidates["workload_score"]
            + WEIGHT_LOCATION_MATCH * candidates["location_match"]
        ).round(4)
        top = candidates.sort_values("match_score", ascending=False).head(3)
        for rank, (_, cand) in enumerate(top.iterrows(), start=1):
            results.append({
                "request_id": req["request_id"], "service_type_name": req["service_type_name"],
                "location_id": req["location_id"], "urgency": req["urgency"],
                "rank": rank, "employee_id": cand["employee_id"], "match_score": cand["match_score"],
            })
    return pd.DataFrame(results)


def run() -> dict:
    con = get_connection()
    matches = score_candidates(con)
    ARTIFACTS_MONITORING.mkdir(parents=True, exist_ok=True)
    matches.to_csv(ARTIFACTS_MONITORING / "skill_match_recommendations.csv", index=False)
    con.close()
    summary = {
        "requests_scored": int(matches["request_id"].nunique()) if len(matches) else 0,
        "avg_top_match_score": round(float(matches[matches["rank"] == 1]["match_score"].mean()), 3) if len(matches) else None,
    }
    log.info("Skill matching summary: %s", summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))
