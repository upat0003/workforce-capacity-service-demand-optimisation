-- dbt test: fails if any weekly overtime mart row has negative overtime hours.
select *
from {{ ref('fct_weekly_overtime') }}
where total_overtime_hours < 0
