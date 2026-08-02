-- Silver: shift and overtime facts, cast and validated against the employee dimension.

CREATE OR REPLACE TABLE silver.fact_shifts AS
SELECT
    shift_id, employee_id,
    try_cast(shift_date AS DATE) AS shift_date,
    upper(trim(location_id)) AS location_id,
    shift_type, planned_start, planned_end, planned_hours, actual_hours, status,
    is_overtime_flag,
    CASE WHEN actual_hours < 0 OR actual_hours > 16 THEN true ELSE false END AS hours_outlier_flag
FROM bronze.shifts
WHERE employee_id IN (SELECT employee_id FROM silver.dim_employee);

CREATE OR REPLACE TABLE silver.fact_overtime AS
SELECT
    employee_id,
    try_cast(week_start_date AS DATE) AS week_start_date,
    rostered_hours, actual_hours_worked, contracted_hours, overtime_hours, overtime_approved_flag
FROM bronze.overtime
WHERE employee_id IN (SELECT employee_id FROM silver.dim_employee);
