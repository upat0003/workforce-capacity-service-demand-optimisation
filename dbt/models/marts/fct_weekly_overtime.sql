{{ config(materialized='table') }}

select
    week_start_date,
    location_id,
    primary_role,
    count(distinct employee_id) as employees_with_overtime,
    sum(overtime_hours) as total_overtime_hours,
    sum(actual_hours_worked) as total_hours_worked,
    sum(contracted_hours) as total_contracted_hours
from {{ ref('int_employee_overtime') }}
group by 1,2,3
