{{ config(materialized='view') }}

-- Joins each service request to its waiting-time and appointment outcome, giving
-- one governed record per request that the demand-forecast and SLA-breach marts build on.
select
    r.request_id,
    r.client_id,
    r.service_type_id,
    r.location_id,
    r.requested_date,
    r.urgency,
    r.complexity_score,
    r.status,
    w.waiting_days_to_schedule,
    w.sla_target_hours,
    w.sla_met_flag
from {{ ref('stg_service_requests') }} r
left join {{ source('bronze', 'waiting_times') }} w using (request_id)
