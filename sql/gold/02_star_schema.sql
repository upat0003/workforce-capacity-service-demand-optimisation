-- Gold: conformed star schema. Dimensions carry business keys and descriptive
-- attributes only; protected attributes (gender, age_band, preferred_language) are kept
-- solely on dim_employee_governed / dim_client for fairness reporting and are excluded
-- from every feature table used in model training (see python/features/feature_engineering.py).

CREATE OR REPLACE TABLE gold.dim_employee AS
SELECT employee_id, primary_role, employment_type, contracted_hours_per_week, fte,
       base_location_id, hire_date, employment_status, manager_id, tenure_years, hourly_rate_band
FROM silver.dim_employee;

CREATE OR REPLACE TABLE gold.dim_employee_governed AS
SELECT employee_id, gender, age_band, primary_role, employment_type, base_location_id
FROM silver.dim_employee;

CREATE OR REPLACE TABLE gold.dim_client AS
SELECT client_id, location_id, client_since_date, complexity_tier, active_flag, consent_data_use_flag
FROM silver.dim_client
WHERE consent_data_use_flag = true;   -- privacy control: exclude clients without data-use consent

CREATE OR REPLACE TABLE gold.dim_location AS SELECT * FROM silver.dim_location;
CREATE OR REPLACE TABLE gold.dim_service_type AS SELECT * FROM silver.dim_service_type;
CREATE OR REPLACE TABLE gold.dim_skill AS SELECT * FROM silver.dim_skill;
CREATE OR REPLACE TABLE gold.dim_case_complexity AS SELECT * FROM silver.dim_case_complexity;

CREATE OR REPLACE TABLE gold.fact_service_requests AS
-- Inner-joined to gold.dim_client (not silver.dim_client) so that a request from a
-- client who has not consented to analytics use is dropped from gold entirely, not
-- merely orphaned -- the fact table's referential integrity mirrors the same privacy
-- control applied to the dimension (see governance/privacy_assessment.md).
SELECT
    r.request_id, r.client_id, r.service_type_id, r.location_id, r.requested_date,
    r.requested_by, r.urgency, r.complexity_score, r.requested_channel, r.status,
    w.waiting_days_to_schedule, w.sla_target_hours, w.sla_met_flag
FROM silver.fact_service_requests r
JOIN gold.dim_client dc USING (client_id)
LEFT JOIN silver.waiting_times w USING (request_id)
WHERE r.client_fk_invalid = false;

CREATE OR REPLACE TABLE gold.fact_appointments AS
-- Inner-joined to gold.fact_service_requests so every appointment traces back to a
-- request from a consented client, keeping the star schema's referential integrity
-- consistent end to end.
SELECT
    a.appointment_id, a.request_id, a.employee_id, a.location_id, a.service_type_id,
    a.scheduled_date, a.status, a.travel_minutes, a.override_flag, a.override_reason,
    c.cancellation_reason, c.cancelled_by, c.notice_hours, c.rebooked_flag,
    o.client_satisfaction_score, o.outcome_quality_score, o.incident_flag,
    o.goal_achieved_flag, o.follow_up_required_flag
FROM silver.fact_appointments a
JOIN gold.fact_service_requests fsr ON fsr.request_id = a.request_id
LEFT JOIN silver.cancellations c USING (appointment_id)
LEFT JOIN silver.fact_outcomes o USING (appointment_id);

CREATE OR REPLACE TABLE gold.fact_shifts AS SELECT * FROM silver.fact_shifts WHERE hours_outlier_flag = false;
CREATE OR REPLACE TABLE gold.fact_overtime AS SELECT * FROM silver.fact_overtime;
