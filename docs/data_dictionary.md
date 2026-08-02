# Data Dictionary

Column-level definitions for every gold-layer table exported to `powerbi/data/`. Source raw
files live in `data/raw/` and `data/reference/`; transformation logic lives in `sql/silver/` and
`sql/gold/`.

## gold.dim_employee

| Column | Type | Description |
|---|---|---|
| employee_id | string | Business key, `EMP-#####` |
| primary_role | string | Support Worker / Team Leader / Coordinator / Allied Health Clinician / Registered Nurse |
| employment_type | string | Full-time / Part-time / Casual |
| contracted_hours_per_week | float | Contracted weekly hours |
| fte | float | Full-time-equivalent (contracted_hours / 38) |
| base_location_id | string | FK to `dim_location` |
| hire_date | date | Date of hire |
| employment_status | string | Active / On Leave / Terminated |
| manager_id | string | FK to `employee_id` of the employee's manager (nullable for leaders) |
| tenure_years | float | Years since hire |
| hourly_rate_band | string | Banded pay rate (Band 1-4, or "Unspecified") |

## gold.dim_employee_governed

Protected-attribute view used only by fairness checks. Never joined into a model feature table.

| Column | Type | Description |
|---|---|---|
| employee_id | string | Business key |
| gender | string | Self-identified gender (Female / Male / Non-binary / Other) |
| age_band | string | Banded age (18-24 ... 65+) |
| primary_role, employment_type, base_location_id | string | Context columns for cohort breakdown |

## gold.dim_client

| Column | Type | Description |
|---|---|---|
| client_id | string | Business key, `CLT-#####` |
| location_id | string | FK to `dim_location` |
| client_since_date | date | Date client relationship began |
| complexity_tier | string | Low / Medium / High / Critical |
| active_flag | boolean | Whether the client is currently active |
| consent_data_use_flag | boolean | Data-use consent (table is pre-filtered to `true` only) |

## gold.dim_location

| Column | Type | Description |
|---|---|---|
| location_id | string | Business key, `LOC-##` |
| region_name | string | Descriptive region name |
| region_type | string | Metro / Growth Area / Regional |
| site_type | string | Office / Community Hub / Depot |

## gold.dim_service_type

| Column | Type | Description |
|---|---|---|
| service_type_id | string | Business key, `SVC-##` |
| service_type_name | string | e.g. "In-Home Support Visit" |
| standard_duration_minutes | int | Standard visit duration |
| requires_skill_id | string | FK to `dim_skill`, nullable |
| complexity_weight | float | Relative complexity multiplier |
| category | string | Personal Support / Clinical / Social Support / Coordination |

## gold.dim_case_complexity

| Column | Type | Description |
|---|---|---|
| complexity_tier | string | Low / Medium / High / Critical |
| score_range | string | Numeric score band (e.g. "26-50") |
| definition | string | Business definition of the tier |
| service_time_multiplier | float | Multiplier applied to standard duration |
| min_skill_level | int | Minimum proficiency level typically required |

## gold.fact_service_requests

| Column | Type | Description |
|---|---|---|
| request_id | string | Business key, `REQ-######` |
| client_id | string | FK to `dim_client` (orphan keys already excluded) |
| service_type_id | string | FK to `dim_service_type` |
| location_id | string | FK to `dim_location` |
| requested_date | date | Date the request was raised |
| requested_by | string | Client / Family Member / Case Manager / GP / Clinician |
| urgency | string | Routine / Priority / Urgent / Emergency |
| complexity_score | float | Continuous complexity score (1-99, may be null) |
| requested_channel | string | Phone / Portal / Referral / Case Manager |
| status | string | Backlog / Scheduled / Completed / Cancelled |
| waiting_days_to_schedule | float | Days between request and scheduled appointment |
| sla_target_hours | float | Response-time SLA target for this request |
| sla_met_flag | boolean | Whether the SLA target was met |

## gold.fact_appointments

| Column | Type | Description |
|---|---|---|
| appointment_id | string | Business key, `APT-######` |
| request_id | string | FK to `fact_service_requests` |
| employee_id | string | FK to `dim_employee` |
| location_id, service_type_id | string | FKs |
| scheduled_date | date | Scheduled visit date |
| status | string | Completed / Cancelled / No-show / Rescheduled |
| travel_minutes | int | Estimated employee travel time |
| override_flag | boolean | Whether a coordinator manually overrode the system match |
| override_reason | string | Reason for override, nullable |
| cancellation_reason, cancelled_by, notice_hours, rebooked_flag | mixed | Populated only when status is Cancelled/No-show |
| client_satisfaction_score | float | 1-5, nullable |
| outcome_quality_score | float | 0-100 |
| incident_flag | boolean | Whether a safety/quality incident was recorded |
| goal_achieved_flag | boolean | Whether the visit's care goal was met |
| follow_up_required_flag | boolean | Whether follow-up action is required |

## gold.fact_shifts / gold.fact_overtime

| Column | Type | Description |
|---|---|---|
| shift_id | string | Business key |
| employee_id | string | FK to `dim_employee` |
| shift_date | date | Rostered date |
| location_id | string | FK to `dim_location` |
| shift_type | string | AM / PM / Night / Split |
| planned_hours, actual_hours | float | Rostered vs. actual worked hours |
| status | string | Completed / Cancelled / No-show |
| is_overtime_flag | boolean | Whether this shift incurred overtime |
| week_start_date | date | ISO week start (fact_overtime grain) |
| contracted_hours, actual_hours_worked, overtime_hours | float | Weekly aggregates (fact_overtime) |
| overtime_approved_flag | boolean | Whether overtime was formally approved |

## Executive / reporting marts

`mart_daily_demand`, `mart_weekly_overtime`, `mart_capacity_utilisation`, `mart_fairness_workload`,
`mart_service_outcomes` and `mart_data_quality` are pre-aggregated for BI consumption; their
column definitions follow directly from the `GROUP BY` clauses in `sql/gold/03_executive_marts.sql`
and `sql/gold/04_data_quality_marts.sql`, and each measure is also documented in
[`metrics_catalogue.md`](metrics_catalogue.md).
