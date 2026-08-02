-- Silver: conformed reference/dimension data. Casing standardised, duplicates removed,
-- surrogate keys kept stable on the natural business key.

CREATE OR REPLACE TABLE silver.dim_location AS
SELECT DISTINCT
    upper(trim(location_id))                       AS location_id,
    trim(region_name)                               AS region_name,
    trim(region_type)                               AS region_type,
    trim(site_type)                                 AS site_type
FROM bronze.locations;

CREATE OR REPLACE TABLE silver.dim_skill AS
SELECT DISTINCT
    upper(trim(skill_id)) AS skill_id,
    trim(skill_name)      AS skill_name,
    trim(skill_category)  AS skill_category,
    mandatory_flag
FROM bronze.skills;

CREATE OR REPLACE TABLE silver.dim_service_type AS
SELECT DISTINCT
    upper(trim(service_type_id)) AS service_type_id,
    trim(service_type_name)      AS service_type_name,
    standard_duration_minutes,
    upper(trim(requires_skill_id)) AS requires_skill_id,
    complexity_weight,
    trim(category)                AS category
FROM bronze.service_types;

CREATE OR REPLACE TABLE silver.dim_case_complexity AS
SELECT DISTINCT
    trim(complexity_tier)      AS complexity_tier,
    score_range,
    definition,
    service_time_multiplier,
    min_skill_level
FROM bronze.case_complexity;

CREATE OR REPLACE TABLE silver.service_level_targets AS
SELECT DISTINCT
    target_id,
    upper(trim(service_type_id)) AS service_type_id,
    upper(trim(location_id))     AS location_id,
    trim(urgency)                AS urgency,
    target_response_hours,
    target_completion_days,
    min_sla_percent
FROM bronze.service_level_targets;
