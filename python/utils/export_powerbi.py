"""Exports gold-layer marts and monitoring/governance artifacts to powerbi/data/
as flat CSVs -- the sample dataset a Power BI report would import or connect to
via a Fabric semantic model in production. See powerbi/semantic_model.md for
how these tables relate to each other.
"""
from __future__ import annotations
import shutil

from .duckdb_conn import get_connection
from .logging_config import get_logger
from .paths import POWERBI_DATA, ARTIFACTS_MONITORING, ensure_dirs

log = get_logger(__name__)

GOLD_TABLES = [
    "dim_employee", "dim_employee_governed", "dim_client", "dim_location", "dim_service_type",
    "dim_skill", "dim_case_complexity", "dim_date",
    "fact_service_requests", "fact_appointments", "fact_shifts", "fact_overtime",
    "mart_daily_demand", "mart_weekly_overtime", "mart_capacity_utilisation",
    "mart_fairness_workload", "mart_service_outcomes", "mart_data_quality",
]

MONITORING_FILES = [
    "demand_forecast_30d.csv", "demand_forecast_30d_org.csv", "shift_recommendations.csv",
    "scheduling_optimiser_assignments.csv", "skill_match_recommendations.csv",
    "scenario_planning.csv", "data_quality_report.csv",
]


def run() -> dict:
    ensure_dirs()
    con = get_connection(read_only=True)
    written = {}
    for table in GOLD_TABLES:
        try:
            df = con.execute(f"SELECT * FROM gold.{table}").fetchdf()
        except Exception as exc:
            log.warning("Skipping export of gold.%s: %s", table, exc)
            continue
        path = POWERBI_DATA / f"{table}.csv"
        df.to_csv(path, index=False)
        written[table] = len(df)
    con.close()

    for fname in MONITORING_FILES:
        src = ARTIFACTS_MONITORING / fname
        if src.exists():
            shutil.copy(src, POWERBI_DATA / fname)
            written[fname] = "copied"

    log.info("Exported %d Power BI sample tables to %s", len(written), POWERBI_DATA)
    return {"tables_exported": len(written), "tables": written}


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2, default=str))
