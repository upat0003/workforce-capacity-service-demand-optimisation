# DAX Measures

Core measure library backing the 8 dashboard pages. Written against the semantic model in
`semantic_model.md`. Grouped by dashboard page; several measures are reused across pages.

## Shared / date intelligence

```dax
Selected Period Requests =
CALCULATE(
    COUNTROWS(fact_service_requests),
    DATESINPERIOD(dim_date[date_key], MAX(dim_date[date_key]), -90, DAY)
)

Prior Period Requests =
CALCULATE(
    [Selected Period Requests],
    DATEADD(dim_date[date_key], -90, DAY)
)

Requests % Change vs Prior Period =
DIVIDE([Selected Period Requests] - [Prior Period Requests], [Prior Period Requests])
```

## 1. Workforce Executive Overview

```dax
Overtime Hours (Trailing 4 Weeks) =
CALCULATE(
    SUM(mart_weekly_overtime[total_overtime_hours]),
    DATESINPERIOD(dim_date[date_key], MAX(dim_date[date_key]), -28, DAY)
)

Open Backlog Requests =
CALCULATE(
    COUNTROWS(fact_service_requests),
    fact_service_requests[status] = "Backlog"
)

SLA Met Rate % =
DIVIDE(
    CALCULATE(COUNTROWS(fact_service_requests), fact_service_requests[sla_met_flag] = TRUE),
    CALCULATE(COUNTROWS(fact_service_requests), NOT ISBLANK(fact_service_requests[sla_met_flag]))
)

Workforce Utilisation % =
DIVIDE(
    SUM(mart_capacity_utilisation[actual_hours]),
    SUM(mart_capacity_utilisation[planned_hours])
)

Executive KPI Status =
SWITCH(
    TRUE(),
    [SLA Met Rate %] < 0.85, "Breach",
    [SLA Met Rate %] < 0.90, "Warning",
    "Healthy"
)
```

## 2. Demand Forecast

```dax
Forecast Requests (Next 30 Days) =
CALCULATE(
    SUM(demand_forecast_30d[forecast_requests]),
    demand_forecast_30d[date_key] > TODAY(),
    demand_forecast_30d[date_key] <= TODAY() + 30
)

Forecast MAPE = SELECTEDVALUE('model_run_summary'[demand_forecasting_mape])
-- populated from artifacts/monitoring/model_run_summary.json via the Power BI dataflow refresh

Model Status Chip =
SWITCH(
    TRUE(),
    [Forecast MAPE] >= 0.25, "Breach",
    [Forecast MAPE] >= 0.18, "Warning",
    "Healthy"
)

Seasonal Uplift % =
VAR WinterAvg = CALCULATE(AVERAGE(mart_daily_demand[requests]), dim_date[month_num] IN {6,7,8})
VAR AnnualAvg = AVERAGE(mart_daily_demand[requests])
RETURN DIVIDE(WinterAvg - AnnualAvg, AnnualAvg)
```

## 3. Capacity and Utilisation

```dax
Capacity Gap FTE =
DIVIDE(
    SUM(mart_weekly_overtime[total_hours_worked]) - SUM(mart_weekly_overtime[total_contracted_hours]),
    38
)

Regions In Shortfall =
CALCULATE(
    DISTINCTCOUNT(dim_location[location_id]),
    FILTER(ALL(dim_location), [Capacity Gap FTE] > 0)
)

Utilisation Band Flag =
VAR U = [Workforce Utilisation %]
RETURN IF(U < 0.78 || U > 0.92, "Out of band", "On target")
```

## 4. Service Backlog

```dax
Average Backlog Age (Days) =
AVERAGEX(
    FILTER(fact_service_requests, fact_service_requests[status] = "Backlog"),
    DATEDIFF(fact_service_requests[requested_date], TODAY(), DAY)
)

Backlog At Risk Count =
CALCULATE(
    COUNTROWS(fact_service_requests),
    fact_service_requests[status] = "Backlog",
    fact_service_requests[breach_risk_score] >= 0.35
)
-- breach_risk_score is written by python/models/service_level_breach_prediction.py during scoring

Backlog Age Flag = IF([Average Backlog Age (Days)] > 7, "Breach", "On track")
```

## 5. Scheduling Recommendations

```dax
Scheduling Fill Rate % =
DIVIDE(
    COUNTROWS(scheduling_optimiser_assignments),
    COUNTROWS(scheduling_optimiser_assignments) + [Requests Unassigned]
)

Avg Top Skill Match Score =
CALCULATE(
    AVERAGE(skill_match_recommendations[match_score]),
    skill_match_recommendations[rank] = 1
)

Recommended Net Shift Change =
SUM(shift_recommendations[recommended_shift_change])
```

## 6. Workforce Fairness

```dax
Workload Gap % (Gender) =
VAR MaxHrs = CALCULATE(MAX(mart_fairness_workload[avg_hours_per_shift]), ALLSELECTED(mart_fairness_workload[gender]))
VAR MinHrs = CALCULATE(MIN(mart_fairness_workload[avg_hours_per_shift]), ALLSELECTED(mart_fairness_workload[gender]))
RETURN DIVIDE(MaxHrs - MinHrs, MinHrs)

Fairness Status =
SWITCH(
    TRUE(),
    [Workload Gap % (Gender)] > 0.25, "Breach",
    [Workload Gap % (Gender)] > 0.15, "Watch",
    "Within threshold"
)

Workload Gini Coefficient = SELECTEDVALUE(scheduling_optimiser_assignments[workload_gini_coefficient])
```

## 7. Service Outcomes

```dax
Avg Client Satisfaction = AVERAGE(mart_service_outcomes[avg_satisfaction])

Incident Rate % =
DIVIDE(SUM(mart_service_outcomes[incident_count]), SUM(mart_service_outcomes[appointments]))

Cancellation Rate % =
DIVIDE(SUM(mart_service_outcomes[cancelled_count]), SUM(mart_service_outcomes[appointments]))

Outcome Alert = IF([Avg Client Satisfaction] < 3.8 || [Incident Rate %] > 0.025, "Review", "OK")
```

## 8. Data Quality and Governance

```dax
DQ Pass Rate % = AVERAGE(data_quality_report[pass_rate_pct]) / 100

Rules Failing = CALCULATE(COUNTROWS(data_quality_report), data_quality_report[status] = "fail")

Models In Breach =
CALCULATE(
    DISTINCTCOUNT('model_run_summary'[model_name]),
    'model_run_summary'[threshold_status] = "breach"
)

Override Rate % = SELECTEDVALUE('override_audit'[override_rate_pct]) / 100

Governance Overall Status =
SWITCH(
    TRUE(),
    [DQ Pass Rate %] < 0.97 || [Models In Breach] > 0, "Action required",
    "Healthy"
)
```
