# Data Catalogue

Business glossary and critical data element (CDE) register for the workforce
capacity and service-demand optimisation platform. Every dataset below exists
as a real, generated file in this repository (`data/raw/`, `data/reference/`,
or a `gold.*` table built by `python/transformation/build_gold.py`).

## Business glossary

| Term | Definition |
|---|---|
| Service request | A demand signal from or on behalf of a client for a scheduled service visit. |
| Appointment | A scheduled, employee-assigned instance of a service request. |
| Backlog | A service request that has not yet been converted into a scheduled appointment. |
| SLA (service-level target) | The maximum response time allowed between a request being raised and being scheduled, by service type, region and urgency. |
| Complexity tier | A client-level classification (Low / Medium / High / Critical) describing the intensity of support required. |
| Overtime | Actual hours worked by an employee in a week beyond their contracted hours. |
| Capacity gap | The difference between the rostered hours available in a region and the hours implied by forecast demand. |
| Workload fairness | The degree to which rostered hours and overtime incidence are evenly distributed across governed employee cohorts. |
| Override | A coordinator's manual change to a system-recommended schedule or match. |

## Critical data elements

| Dataset | Grain | Owner | Sensitivity | Source table |
|---|---|---|---|---|
| employees | 1 row per employee | People & Culture | Internal - contains employment attributes | `data/raw/employees.csv` → `gold.dim_employee` |
| employee_skills | 1 row per employee-skill | People & Culture | Internal | `gold.dim_skill` / `silver.employee_skills` |
| clients | 1 row per client | Service Delivery | Restricted - pseudonymous client record | `gold.dim_client` (consent-filtered) |
| service_requests | 1 row per request | Service Delivery | Restricted | `gold.fact_service_requests` |
| appointments | 1 row per appointment | Service Delivery / Scheduling | Restricted | `gold.fact_appointments` |
| shifts | 1 row per rostered shift | Workforce Planning | Internal | `gold.fact_shifts` |
| overtime | 1 row per employee-week | Workforce Planning | Internal | `gold.fact_overtime` |
| outcomes | 1 row per completed appointment | Quality & Safety | Restricted - includes incident flags | joined into `gold.fact_appointments` |
| service_level_targets | 1 row per service type / region / urgency | Service Delivery | Internal (reference) | `gold.dim_service_type` join |

## Dataset directory

| File | Rows (dev-mode) | Description |
|---|---|---|
| `data/reference/locations.csv` | 10 | Regional site master (metro, growth-corridor and regional Victoria sites) |
| `data/reference/skills.csv` | 14 | Skill/competency register |
| `data/reference/service_types.csv` | 9 | Service catalogue, standard duration and complexity weight |
| `data/reference/case_complexity.csv` | 4 | Complexity tier definitions and service-time multipliers |
| `data/reference/service_level_targets.csv` | 360 | SLA targets by service type, region and urgency |
| `data/raw/employees.csv` | ~150 | Employee master (includes intentional duplicate rows for silver-layer dedup) |
| `data/raw/employee_skills.csv` | ~800 | Employee-to-skill bridge with certification expiry |
| `data/raw/availability.csv` | ~1,300 | Weekly recurring availability patterns plus date-specific exceptions |
| `data/raw/leave.csv` | ~640 | Leave requests and approval status |
| `data/raw/clients.csv` | ~520 | Client master (pseudonymous IDs only, consent flag) |
| `data/raw/service_requests.csv` | ~7,000-7,500 | Demand records over a 12-month history |
| `data/raw/shifts.csv` | ~17,000 | Rostered shift instances |
| `data/raw/overtime.csv` | ~5,500 | Employee-week rostered vs. actual hours |
| `data/raw/appointments.csv` | ~6,900-7,100 | Scheduled service visits |
| `data/raw/waiting_times.csv` | ~6,900-7,100 | Request-to-schedule wait time and SLA outcome |
| `data/raw/cancellations.csv` | ~1,000-1,200 | Cancellation and no-show detail |
| `data/raw/outcomes.csv` | ~5,200-5,700 | Client satisfaction and service-quality outcomes |

See [`docs/data_dictionary.md`](../docs/data_dictionary.md) for full column-level definitions and
[`lineage.md`](lineage.md) for how each dataset flows through bronze, silver and gold.
