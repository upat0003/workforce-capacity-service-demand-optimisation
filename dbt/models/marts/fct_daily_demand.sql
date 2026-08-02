{{ config(materialized='table') }}

-- Star-schema fact powering the Demand Forecast and Service Backlog dashboard pages.
select
    requested_date as date_key,
    location_id,
    service_type_id,
    urgency,
    count(*) as requests,
    avg(complexity_score) as avg_complexity_score,
    sum(case when sla_met_flag then 1 else 0 end) as sla_met_count,
    sum(case when status = 'Backlog' then 1 else 0 end) as backlog_count
from {{ ref('int_request_wait_times') }}
group by 1,2,3,4
