-- Gold: data-quality summary mart, aggregating the row-level flags raised in silver
-- into a single control-friendly table for the governance dashboard.

CREATE OR REPLACE TABLE gold.mart_data_quality AS
SELECT 'employees' AS dataset, 'location_fk_invalid' AS rule, count(*) FILTER (WHERE location_fk_invalid) AS failing_rows, count(*) AS total_rows
FROM silver.dim_employee
UNION ALL
SELECT 'service_requests', 'client_fk_invalid', count(*) FILTER (WHERE client_fk_invalid), count(*)
FROM silver.fact_service_requests
UNION ALL
SELECT 'service_requests', 'complexity_score_missing', count(*) FILTER (WHERE complexity_score_missing), count(*)
FROM silver.fact_service_requests
UNION ALL
SELECT 'shifts', 'hours_outlier', count(*) FILTER (WHERE hours_outlier_flag), count(*)
FROM silver.fact_shifts
UNION ALL
SELECT 'employee_skills', 'certification_expired', count(*) FILTER (WHERE expired_flag), count(*)
FROM silver.employee_skills;
