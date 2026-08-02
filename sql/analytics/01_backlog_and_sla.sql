-- Analytics: ad hoc query answering "where is the current service backlog concentrated?"
-- Used by python/monitoring and referenced in powerbi/dashboard_specification.md (Service Backlog page).
SELECT
    location_id,
    service_type_id,
    urgency,
    count(*) AS open_backlog_requests,
    avg(datediff('day', requested_date, current_date)) AS avg_days_open
FROM gold.fact_service_requests
WHERE status = 'Backlog'
GROUP BY 1,2,3
ORDER BY open_backlog_requests DESC;
