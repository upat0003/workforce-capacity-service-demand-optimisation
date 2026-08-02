{{ config(materialized='view') }}

-- Deduplicated, conformed employee master. Mirrors sql/silver/02_dim_employee.sql
-- so the dbt lineage graph documents the same transformation the local pipeline runs.
with ranked as (
    select
        employee_id,
        primary_role,
        employment_type,
        contracted_hours_per_week,
        fte,
        upper(trim(base_location_id)) as base_location_id,
        try_cast(hire_date as date) as hire_date,
        employment_status,
        manager_id,
        gender,
        age_band,
        coalesce(hourly_rate_band, 'Unspecified') as hourly_rate_band,
        row_number() over (partition by employee_id order by _ingested_at desc) as rn
    from {{ source('bronze', 'employees') }}
)
select
    employee_id, primary_role, employment_type, contracted_hours_per_week, fte,
    base_location_id, hire_date, employment_status, manager_id, gender, age_band, hourly_rate_band
from ranked
where rn = 1
