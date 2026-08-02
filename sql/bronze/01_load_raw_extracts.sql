-- Bronze layer: immutable, append-friendly landing of source extracts.
-- In production (Microsoft Fabric) these would be Lakehouse Delta tables populated by
-- a Data Factory pipeline landing files from source systems (rostering, CRM, telephony).
-- Locally, DuckDB reads the synthetic CSV extracts directly and stamps ingestion metadata.
-- Paths are substituted by python/transformation/build_bronze.py at execution time.

CREATE OR REPLACE TABLE bronze.locations AS
SELECT *, now() AS _ingested_at, 'locations.csv' AS _source_file
FROM read_csv_auto('{reference_dir}/locations.csv', union_by_name=true);

CREATE OR REPLACE TABLE bronze.skills AS
SELECT *, now() AS _ingested_at, 'skills.csv' AS _source_file
FROM read_csv_auto('{reference_dir}/skills.csv', union_by_name=true);

CREATE OR REPLACE TABLE bronze.service_types AS
SELECT *, now() AS _ingested_at, 'service_types.csv' AS _source_file
FROM read_csv_auto('{reference_dir}/service_types.csv', union_by_name=true);

CREATE OR REPLACE TABLE bronze.case_complexity AS
SELECT *, now() AS _ingested_at, 'case_complexity.csv' AS _source_file
FROM read_csv_auto('{reference_dir}/case_complexity.csv', union_by_name=true);

CREATE OR REPLACE TABLE bronze.service_level_targets AS
SELECT *, now() AS _ingested_at, 'service_level_targets.csv' AS _source_file
FROM read_csv_auto('{reference_dir}/service_level_targets.csv', union_by_name=true);

CREATE OR REPLACE TABLE bronze.employees AS
SELECT *, now() AS _ingested_at, 'employees.csv' AS _source_file
FROM read_csv_auto('{raw_dir}/employees.csv', union_by_name=true);

CREATE OR REPLACE TABLE bronze.employee_skills AS
SELECT *, now() AS _ingested_at, 'employee_skills.csv' AS _source_file
FROM read_csv_auto('{raw_dir}/employee_skills.csv', union_by_name=true);

CREATE OR REPLACE TABLE bronze.availability AS
SELECT *, now() AS _ingested_at, 'availability.csv' AS _source_file
FROM read_csv_auto('{raw_dir}/availability.csv', union_by_name=true);

CREATE OR REPLACE TABLE bronze.leave AS
SELECT *, now() AS _ingested_at, 'leave.csv' AS _source_file
FROM read_csv_auto('{raw_dir}/leave.csv', union_by_name=true);

CREATE OR REPLACE TABLE bronze.clients AS
SELECT *, now() AS _ingested_at, 'clients.csv' AS _source_file
FROM read_csv_auto('{raw_dir}/clients.csv', union_by_name=true);

CREATE OR REPLACE TABLE bronze.service_requests AS
SELECT *, now() AS _ingested_at, 'service_requests.csv' AS _source_file
FROM read_csv_auto('{raw_dir}/service_requests.csv', union_by_name=true);

CREATE OR REPLACE TABLE bronze.shifts AS
SELECT *, now() AS _ingested_at, 'shifts.csv' AS _source_file
FROM read_csv_auto('{raw_dir}/shifts.csv', union_by_name=true);

CREATE OR REPLACE TABLE bronze.overtime AS
SELECT *, now() AS _ingested_at, 'overtime.csv' AS _source_file
FROM read_csv_auto('{raw_dir}/overtime.csv', union_by_name=true);

CREATE OR REPLACE TABLE bronze.appointments AS
SELECT *, now() AS _ingested_at, 'appointments.csv' AS _source_file
FROM read_csv_auto('{raw_dir}/appointments.csv', union_by_name=true);

CREATE OR REPLACE TABLE bronze.waiting_times AS
SELECT *, now() AS _ingested_at, 'waiting_times.csv' AS _source_file
FROM read_csv_auto('{raw_dir}/waiting_times.csv', union_by_name=true);

CREATE OR REPLACE TABLE bronze.cancellations AS
SELECT *, now() AS _ingested_at, 'cancellations.csv' AS _source_file
FROM read_csv_auto('{raw_dir}/cancellations.csv', union_by_name=true);

CREATE OR REPLACE TABLE bronze.outcomes AS
SELECT *, now() AS _ingested_at, 'outcomes.csv' AS _source_file
FROM read_csv_auto('{raw_dir}/outcomes.csv', union_by_name=true);
