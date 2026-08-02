-- dbt test: fails if any request carries a non-positive SLA target, which would
-- indicate a broken join to the service_level_targets reference table.
select *
from {{ ref('int_request_wait_times') }}
where sla_target_hours is not null and sla_target_hours <= 0
