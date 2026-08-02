"""Scheduling optimiser: a constrained greedy heuristic that assigns available,
skill-eligible employees to a day's open service requests while respecting a
daily hours cap and actively balancing workload across staff. This is
deliberately not a commercial MIP/CP-SAT solver -- it is a transparent,
auditable greedy assignment that a coordinator can reason about and override,
which matters for the human-in-the-loop control described in
governance/model_card.md.

Assignment order: requests are processed most-urgent-first; for each request,
the eligible candidate with the lowest running daily-hours total is chosen
(a simple longest-processing-time-style load-balancing heuristic), breaking
ties on travel/location match.
"""
from __future__ import annotations
import json
import pandas as pd
import numpy as np

from ..utils.duckdb_conn import get_connection
from ..utils.logging_config import get_logger
from ..utils.paths import ARTIFACTS_MONITORING

log = get_logger(__name__)

MAX_DAILY_HOURS = 8.0
URGENCY_ORDER = {"Emergency": 0, "Urgent": 1, "Priority": 2, "Routine": 3}


def _gini(x: np.ndarray) -> float:
    if len(x) == 0 or np.all(x == 0):
        return 0.0
    x = np.sort(x)
    n = len(x)
    cum = np.cumsum(x)
    return float((n + 1 - 2 * np.sum(cum) / cum[-1]) / n)


def optimise_day(requests: pd.DataFrame, employees: pd.DataFrame, skills: pd.DataFrame,
                  service_types: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    requests = requests.copy()
    requests["urgency_rank"] = requests["urgency"].map(URGENCY_ORDER).fillna(3)
    requests = requests.sort_values(["urgency_rank", "complexity_score"], ascending=[True, False])

    svc_duration = service_types.set_index("service_type_id")["standard_duration_minutes"].to_dict()
    svc_skill = service_types.set_index("service_type_id")["requires_skill_id"].to_dict()
    skill_by_emp = skills.groupby("employee_id")["skill_id"].apply(set).to_dict()

    daily_hours = {eid: 0.0 for eid in employees["employee_id"]}
    emp_location = employees.set_index("employee_id")["base_location_id"].to_dict()

    assignments = []
    unassigned = 0
    for _, req in requests.iterrows():
        duration_hours = svc_duration.get(req["service_type_id"], 60) / 60.0
        required_skill = svc_skill.get(req["service_type_id"])
        eligible = [
            eid for eid in employees["employee_id"]
            if daily_hours[eid] + duration_hours <= MAX_DAILY_HOURS
            and (pd.isna(required_skill) or required_skill in skill_by_emp.get(eid, set()))
        ]
        if not eligible:
            unassigned += 1
            continue
        eligible.sort(key=lambda eid: (daily_hours[eid], emp_location.get(eid) != req["location_id"]))
        chosen = eligible[0]
        daily_hours[chosen] += duration_hours
        assignments.append({
            "request_id": req["request_id"], "employee_id": chosen,
            "service_type_id": req["service_type_id"], "location_id": req["location_id"],
            "urgency": req["urgency"], "assigned_hours": round(duration_hours, 2),
        })

    hours_array = np.array(list(daily_hours.values()))
    metrics = {
        "requests_considered": int(len(requests)),
        "requests_assigned": int(len(assignments)),
        "requests_unassigned": int(unassigned),
        "fill_rate_pct": round(100 * len(assignments) / max(1, len(requests)), 1),
        "avg_hours_per_active_employee": round(float(hours_array[hours_array > 0].mean()), 2) if (hours_array > 0).any() else 0.0,
        "workload_gini_coefficient": round(_gini(hours_array), 3),
        "employees_utilised": int((hours_array > 0).sum()),
        "employees_available": int(len(employees)),
    }
    return pd.DataFrame(assignments), metrics


def run() -> dict:
    con = get_connection()
    target_day = con.execute("SELECT max(requested_date) FROM gold.fact_service_requests WHERE status='Backlog'").fetchone()[0]
    if target_day is None:
        target_day = con.execute("SELECT max(requested_date) FROM gold.fact_service_requests").fetchone()[0]

    requests = con.execute("""
        SELECT request_id, service_type_id, location_id, urgency, complexity_score
        FROM gold.fact_service_requests
        WHERE status = 'Backlog'
    """).fetchdf()
    if len(requests) == 0:
        requests = con.execute("""
            SELECT request_id, service_type_id, location_id, urgency, complexity_score
            FROM gold.fact_service_requests ORDER BY requested_date DESC LIMIT 150
        """).fetchdf()
    requests["complexity_score"] = requests["complexity_score"].fillna(30)

    employees = con.execute("SELECT employee_id, base_location_id FROM gold.dim_employee WHERE employment_status='Active'").fetchdf()
    skills = con.execute("SELECT employee_id, skill_id FROM silver.employee_skills WHERE expired_flag = false").fetchdf()
    service_types = con.execute("SELECT service_type_id, standard_duration_minutes, requires_skill_id FROM gold.dim_service_type").fetchdf()
    con.close()

    assignments, metrics = optimise_day(requests, employees, skills, service_types)
    ARTIFACTS_MONITORING.mkdir(parents=True, exist_ok=True)
    assignments.to_csv(ARTIFACTS_MONITORING / "scheduling_optimiser_assignments.csv", index=False)

    log.info("Scheduling optimiser metrics: %s", metrics)
    return metrics


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))
