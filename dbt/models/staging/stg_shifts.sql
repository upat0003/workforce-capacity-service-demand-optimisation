{{ config(materialized='view') }}

select
    shift_id,
    employee_id,
    try_cast(shift_date as date) as shift_date,
    upper(trim(location_id)) as location_id,
    shift_type,
    planned_hours,
    actual_hours,
    status,
    is_overtime_flag,
    case when actual_hours < 0 or actual_hours > 16 then true else false end as hours_outlier_flag
from {{ source('bronze', 'shifts') }}
