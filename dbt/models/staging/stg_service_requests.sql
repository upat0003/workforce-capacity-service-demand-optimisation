{{ config(materialized='view') }}

select
    request_id,
    client_id,
    upper(trim(service_type_id)) as service_type_id,
    upper(trim(location_id)) as location_id,
    try_cast(requested_date as date) as requested_date,
    requested_by,
    urgency,
    complexity_score,
    case when complexity_score is null then true else false end as complexity_score_missing,
    requested_channel,
    status
from {{ source('bronze', 'service_requests') }}
