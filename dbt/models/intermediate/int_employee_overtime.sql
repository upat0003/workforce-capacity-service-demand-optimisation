{{ config(materialized='view') }}

select
    e.employee_id,
    e.primary_role,
    e.base_location_id as location_id,
    o.week_start_date,
    o.contracted_hours,
    o.actual_hours_worked,
    o.overtime_hours,
    o.overtime_approved_flag
from {{ ref('stg_employees') }} e
join {{ source('bronze', 'overtime') }} o using (employee_id)
