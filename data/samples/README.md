# Data Samples

Small, static previews (20 rows, or the full reference table where it is already short) of the
key synthetic datasets, committed to the repository so the data shape is visible without running
the pipeline. These are a convenience snapshot only -- the authoritative datasets are regenerated
by `python -m python.ingestion.generate_synthetic_data` into `data/raw/` and `data/reference/`,
and are themselves already lightweight enough to commit in full (see the repository as shipped).

| File | Source table |
|---|---|
| `employees_sample.csv` | `data/raw/employees.csv` |
| `clients_sample.csv` | `data/raw/clients.csv` |
| `service_requests_sample.csv` | `data/raw/service_requests.csv` |
| `appointments_sample.csv` | `data/raw/appointments.csv` |
| `shifts_sample.csv` | `data/raw/shifts.csv` |
| `overtime_sample.csv` | `data/raw/overtime.csv` |
| `locations_sample.csv` | `data/reference/locations.csv` (full table, 10 rows) |
| `skills_sample.csv` | `data/reference/skills.csv` (full table, 14 rows) |
| `service_types_sample.csv` | `data/reference/service_types.csv` (full table, 9 rows) |
| `case_complexity_sample.csv` | `data/reference/case_complexity.csv` (full table, 4 rows) |
