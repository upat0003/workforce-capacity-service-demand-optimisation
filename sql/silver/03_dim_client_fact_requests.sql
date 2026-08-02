-- Silver: client master and service-request facts, with referential integrity flags
-- surfaced rather than silently dropped, so data-quality controls can act on them.

CREATE OR REPLACE TABLE silver.dim_client AS
SELECT DISTINCT
    client_id,
    upper(trim(location_id)) AS location_id,
    try_cast(client_since_date AS DATE) AS client_since_date,
    complexity_tier,
    coalesce(preferred_language, 'Not recorded') AS preferred_language,
    active_flag,
    consent_data_use_flag,
    communication_preference
FROM bronze.clients;

CREATE OR REPLACE TABLE silver.fact_service_requests AS
SELECT
    r.request_id,
    r.client_id,
    CASE WHEN r.client_id IN (SELECT client_id FROM silver.dim_client) THEN false ELSE true END AS client_fk_invalid,
    upper(trim(r.service_type_id)) AS service_type_id,
    upper(trim(r.location_id))     AS location_id,
    try_cast(r.requested_date AS DATE) AS requested_date,
    r.requested_by,
    r.urgency,
    r.complexity_score,
    CASE WHEN r.complexity_score IS NULL THEN true ELSE false END AS complexity_score_missing,
    r.requested_channel,
    r.status
FROM bronze.service_requests r;
