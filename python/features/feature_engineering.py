"""Builds model-ready feature tables from the gold layer and writes them to
data/processed/ as CSV. Every feature table here deliberately excludes the
protected attributes carried on gold.dim_employee_governed (gender, age_band,
preferred_language) -- those are reserved for governance/fairness_checks.py and
are never joined into a training frame. See governance/model_card.md.

Run standalone with:
    python -m python.features.feature_engineering
"""
from __future__ import annotations
import pandas as pd

from ..utils.duckdb_conn import get_connection
from ..utils.logging_config import get_logger
from ..utils.paths import DATA_PROCESSED, ensure_dirs

log = get_logger(__name__)


def _add_calendar_features(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    d = pd.to_datetime(df[date_col])
    df["day_of_week"] = d.dt.dayofweek
    df["is_weekend"] = (d.dt.dayofweek >= 5).astype(int)
    df["month"] = d.dt.month
    df["is_winter"] = d.dt.month.isin([6, 7, 8]).astype(int)
    df["week_of_year"] = d.dt.isocalendar().week.astype(int)
    df["day_index"] = (d - d.min()).dt.days
    return df


def build_demand_features(con) -> pd.DataFrame:
    """Organisation-wide daily demand series, with lag and rolling features for the
    demand-forecasting model. Forecasting is done top-down at the organisation level
    because individual-region daily counts are too sparse (a handful of requests per
    day) for a stable percentage-error metric; build_demand_location_shares() below
    supplies the trailing regional mix used to allocate the organisation forecast
    back down to each region for the Power BI regional view."""
    daily = con.execute("""
        SELECT date_key, sum(requests) AS requests,
               avg(avg_complexity_score) AS avg_complexity_score,
               sum(backlog_count) AS backlog_count,
               sum(sla_met_count) AS sla_met_count
        FROM gold.mart_daily_demand
        GROUP BY 1
        ORDER BY 1
    """).fetchdf()
    daily = _add_calendar_features(daily, "date_key")
    daily = daily.sort_values("date_key").reset_index(drop=True)
    daily["lag_1"] = daily["requests"].shift(1)
    daily["lag_7"] = daily["requests"].shift(7)
    daily["rolling_mean_7"] = daily["requests"].shift(1).rolling(7).mean()
    daily["rolling_mean_28"] = daily["requests"].shift(1).rolling(28).mean()
    daily = daily.dropna(subset=["lag_7", "rolling_mean_28"]).reset_index(drop=True)
    return daily


def build_demand_location_shares(con, trailing_days: int = 56) -> pd.DataFrame:
    """Trailing share of organisation-wide demand attributable to each region,
    used to allocate the top-down forecast back to a regional view."""
    df = con.execute(f"""
        WITH recent AS (
            SELECT location_id, sum(requests) AS requests
            FROM gold.mart_daily_demand
            WHERE date_key > (SELECT max(date_key) FROM gold.mart_daily_demand) - INTERVAL {trailing_days} DAY
            GROUP BY 1
        )
        SELECT location_id, requests, requests * 1.0 / sum(requests) OVER () AS share
        FROM recent
        ORDER BY share DESC
    """).fetchdf()
    return df


def build_complexity_features(con) -> pd.DataFrame:
    """Request-level features for predicting complexity tier / score at intake,
    before a coordinator has manually triaged the request."""
    df = con.execute("""
        SELECT r.request_id, r.location_id, r.service_type_id, r.urgency,
               r.requested_by, r.requested_channel, r.requested_date,
               r.complexity_score, c.complexity_tier
        FROM gold.fact_service_requests r
        JOIN gold.dim_client c USING (client_id)
        WHERE r.complexity_score IS NOT NULL
    """).fetchdf()
    df = _add_calendar_features(df, "requested_date")
    return df


def build_cancellation_features(con) -> pd.DataFrame:
    """Appointment-level features for predicting cancellation / no-show risk."""
    df = con.execute("""
        SELECT a.appointment_id, a.location_id, a.service_type_id, a.scheduled_date,
               a.travel_minutes, a.override_flag,
               r.urgency, r.complexity_score,
               CASE WHEN a.status IN ('Cancelled','No-show') THEN 1 ELSE 0 END AS cancelled_label
        FROM gold.fact_appointments a
        JOIN gold.fact_service_requests r USING (request_id)
    """).fetchdf()
    df = _add_calendar_features(df, "scheduled_date")
    df["complexity_score"] = df["complexity_score"].fillna(df["complexity_score"].median())
    return df


def build_sla_breach_features(con) -> pd.DataFrame:
    """Request-level features for predicting SLA breach risk at intake time."""
    df = con.execute("""
        SELECT request_id, location_id, service_type_id, urgency, complexity_score,
               requested_date, sla_target_hours, sla_met_flag
        FROM gold.fact_service_requests
        WHERE sla_met_flag IS NOT NULL
    """).fetchdf()
    df = _add_calendar_features(df, "requested_date")
    df["complexity_score"] = df["complexity_score"].fillna(df["complexity_score"].median())
    df["breach_label"] = (~df["sla_met_flag"].astype(bool)).astype(int)
    return df


def build_workload_capacity_features(con) -> pd.DataFrame:
    """Region-week level features joining rostered capacity to demand, used for
    workload estimation and capacity-gap prediction."""
    df = con.execute("""
        WITH demand AS (
            SELECT date_trunc('week', date_key)::DATE AS week_start_date, location_id,
                   sum(requests) AS requests, avg(avg_complexity_score) AS avg_complexity_score
            FROM gold.mart_daily_demand GROUP BY 1,2
        ),
        capacity AS (
            SELECT week_start_date, location_id,
                   sum(total_hours_worked) AS total_hours_worked,
                   sum(total_contracted_hours) AS total_contracted_hours,
                   sum(total_overtime_hours) AS total_overtime_hours,
                   count(DISTINCT employees_with_overtime) AS employees_with_overtime
            FROM gold.mart_weekly_overtime GROUP BY 1,2
        )
        SELECT d.week_start_date, d.location_id, d.requests, d.avg_complexity_score,
               c.total_hours_worked, c.total_contracted_hours, c.total_overtime_hours
        FROM demand d
        JOIN capacity c USING (week_start_date, location_id)
        ORDER BY 1,2
    """).fetchdf()
    df["required_hours_estimate"] = df["requests"] * df["avg_complexity_score"].fillna(30) / 30 * 1.1
    df["capacity_gap_hours"] = df["required_hours_estimate"] - df["total_contracted_hours"]
    df["capacity_gap_fte"] = df["capacity_gap_hours"] / 38.0
    df["week_index"] = (pd.to_datetime(df["week_start_date"]) - pd.to_datetime(df["week_start_date"]).min()).dt.days // 7
    df["month"] = pd.to_datetime(df["week_start_date"]).dt.month
    return df


def run() -> dict[str, int]:
    ensure_dirs()
    con = get_connection()
    tables = {
        "demand_features": build_demand_features(con),
        "demand_location_shares": build_demand_location_shares(con),
        "complexity_features": build_complexity_features(con),
        "cancellation_features": build_cancellation_features(con),
        "sla_breach_features": build_sla_breach_features(con),
        "workload_capacity_features": build_workload_capacity_features(con),
    }
    counts = {}
    for name, df in tables.items():
        path = DATA_PROCESSED / f"{name}.csv"
        df.to_csv(path, index=False)
        counts[name] = len(df)
        log.info("wrote %-28s %6d rows -> %s", name, len(df), path.name)
    con.close()
    return counts


if __name__ == "__main__":
    counts = run()
    for k, v in counts.items():
        print(f"{k:28s} {v:8,d} rows")
