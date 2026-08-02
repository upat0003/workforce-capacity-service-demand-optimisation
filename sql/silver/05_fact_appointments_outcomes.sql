-- Silver: appointment, waiting-time, cancellation and outcome facts joined back to
-- their governing service request.

CREATE OR REPLACE TABLE silver.fact_appointments AS
SELECT
    a.appointment_id, a.request_id, a.employee_id,
    upper(trim(a.location_id)) AS location_id,
    upper(trim(a.service_type_id)) AS service_type_id,
    try_cast(a.scheduled_date AS DATE) AS scheduled_date,
    a.scheduled_start, a.status, a.travel_minutes, a.override_flag, a.override_reason
FROM bronze.appointments a;

CREATE OR REPLACE TABLE silver.waiting_times AS
SELECT
    request_id,
    try_cast(requested_date AS DATE) AS requested_date,
    try_cast(scheduled_date AS DATE) AS scheduled_date,
    try_cast(completed_date AS DATE) AS completed_date,
    waiting_hours_to_schedule, waiting_days_to_schedule, sla_target_hours, sla_met_flag
FROM bronze.waiting_times;

CREATE OR REPLACE TABLE silver.cancellations AS
SELECT
    cancellation_id, appointment_id, cancelled_by, cancellation_reason, notice_hours, rebooked_flag
FROM bronze.cancellations;

CREATE OR REPLACE TABLE silver.fact_outcomes AS
SELECT
    outcome_id, appointment_id, client_satisfaction_score, outcome_quality_score,
    incident_flag, incident_severity, goal_achieved_flag, follow_up_required_flag
FROM bronze.outcomes;
