-- Silver: employee master, deduplicated on employee_id (keep most recently ingested row),
-- location codes normalised, protected attributes retained but tagged for governed use only.

CREATE OR REPLACE TABLE silver.dim_employee AS
WITH ranked AS (
    SELECT
        employee_id,
        primary_role,
        employment_type,
        contracted_hours_per_week,
        fte,
        upper(trim(base_location_id))                        AS base_location_id,
        try_cast(hire_date AS DATE)                          AS hire_date,
        employment_status,
        manager_id,
        gender,
        age_band,
        coalesce(hourly_rate_band, 'Unspecified')             AS hourly_rate_band,
        _ingested_at,
        row_number() OVER (PARTITION BY employee_id ORDER BY _ingested_at DESC) AS rn
    FROM bronze.employees
)
SELECT
    employee_id, primary_role, employment_type, contracted_hours_per_week, fte,
    base_location_id, hire_date, employment_status, manager_id, gender, age_band,
    hourly_rate_band,
    datediff('day', hire_date, current_date) / 365.25 AS tenure_years,
    CASE WHEN base_location_id NOT IN (SELECT location_id FROM silver.dim_location) THEN true ELSE false END AS location_fk_invalid
FROM ranked
WHERE rn = 1;

CREATE OR REPLACE TABLE silver.employee_skills AS
SELECT
    employee_id,
    upper(trim(skill_id)) AS skill_id,
    proficiency_level,
    try_cast(certified_date AS DATE) AS certified_date,
    try_cast(expiry_date AS DATE)    AS expiry_date,
    expired_flag
FROM bronze.employee_skills
WHERE employee_id IN (SELECT employee_id FROM silver.dim_employee);

CREATE OR REPLACE TABLE silver.availability AS
SELECT
    employee_id, pattern_type, try_cast(specific_date AS DATE) AS specific_date,
    day_of_week, available_flag, earliest_start, latest_end, preferred_shift_type
FROM bronze.availability
WHERE employee_id IN (SELECT employee_id FROM silver.dim_employee);

CREATE OR REPLACE TABLE silver.leave AS
SELECT
    leave_id, employee_id, upper(trim(leave_type)) AS leave_type,
    try_cast(start_date AS DATE) AS start_date,
    try_cast(end_date AS DATE)   AS end_date,
    status, approved_by, try_cast(requested_date AS DATE) AS requested_date
FROM bronze.leave
WHERE employee_id IN (SELECT employee_id FROM silver.dim_employee);
