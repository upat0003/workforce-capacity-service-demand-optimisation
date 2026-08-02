-- Gold: aggregated marts feeding the Power BI semantic model and executive reporting.

CREATE OR REPLACE TABLE gold.mart_daily_demand AS
SELECT
    requested_date AS date_key,
    location_id,
    service_type_id,
    urgency,
    count(*) AS requests,
    avg(complexity_score) AS avg_complexity_score,
    sum(CASE WHEN sla_met_flag THEN 1 ELSE 0 END) AS sla_met_count,
    sum(CASE WHEN status = 'Backlog' THEN 1 ELSE 0 END) AS backlog_count
FROM gold.fact_service_requests
GROUP BY 1,2,3,4;

CREATE OR REPLACE TABLE gold.mart_weekly_overtime AS
SELECT
    week_start_date,
    e.base_location_id AS location_id,
    e.primary_role,
    count(DISTINCT ot.employee_id) AS employees_with_overtime,
    sum(ot.overtime_hours) AS total_overtime_hours,
    avg(ot.overtime_hours) AS avg_overtime_hours,
    sum(ot.actual_hours_worked) AS total_hours_worked,
    sum(ot.contracted_hours) AS total_contracted_hours
FROM gold.fact_overtime ot
JOIN gold.dim_employee e USING (employee_id)
GROUP BY 1,2,3;

CREATE OR REPLACE TABLE gold.mart_capacity_utilisation AS
SELECT
    s.shift_date AS date_key,
    s.location_id,
    e.primary_role,
    count(*) AS shifts_rostered,
    sum(CASE WHEN s.status = 'Completed' THEN 1 ELSE 0 END) AS shifts_completed,
    sum(s.actual_hours) AS actual_hours,
    sum(s.planned_hours) AS planned_hours,
    sum(CASE WHEN s.is_overtime_flag THEN 1 ELSE 0 END) AS overtime_shifts
FROM gold.fact_shifts s
JOIN gold.dim_employee e USING (employee_id)
GROUP BY 1,2,3;

CREATE OR REPLACE TABLE gold.mart_fairness_workload AS
SELECT
    g.gender,
    g.age_band,
    g.primary_role,
    g.base_location_id AS location_id,
    count(*) AS shift_count,
    sum(s.actual_hours) AS total_actual_hours,
    sum(CASE WHEN s.is_overtime_flag THEN 1 ELSE 0 END) AS overtime_shift_count
FROM gold.fact_shifts s
JOIN gold.dim_employee_governed g USING (employee_id)
GROUP BY 1,2,3,4
HAVING count(*) >= 8;  -- small-number suppression rule (see governance/privacy_assessment.md)

CREATE OR REPLACE TABLE gold.mart_service_outcomes AS
SELECT
    a.location_id, a.service_type_id,
    date_trunc('month', a.scheduled_date)::DATE AS month_start_date,
    count(*) AS appointments,
    avg(a.client_satisfaction_score) AS avg_satisfaction,
    avg(a.outcome_quality_score) AS avg_quality_score,
    sum(CASE WHEN a.incident_flag THEN 1 ELSE 0 END) AS incident_count,
    sum(CASE WHEN a.status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_count,
    sum(CASE WHEN a.goal_achieved_flag THEN 1 ELSE 0 END) AS goals_achieved_count
FROM gold.fact_appointments a
GROUP BY 1,2,3;
