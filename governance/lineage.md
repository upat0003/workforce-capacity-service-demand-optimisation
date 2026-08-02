# Data Lineage

## End-to-end flow

```mermaid
flowchart LR
    subgraph Source["Source systems (synthetic)"]
        A1["Rostering extract"]
        A2["CRM / client & request extract"]
        A3["Reference data (locations, skills, service types, SLA targets)"]
    end

    subgraph Bronze["Bronze - data/raw, data/reference -> bronze.*"]
        B1["bronze.employees, availability, leave, shifts, overtime"]
        B2["bronze.clients, service_requests, appointments, waiting_times, cancellations, outcomes"]
        B3["bronze.locations, skills, service_types, case_complexity, service_level_targets"]
    end

    subgraph Silver["Silver - cleaned & conformed"]
        C1["silver.dim_employee (deduplicated)"]
        C2["silver.dim_client, fact_service_requests (FK validated)"]
        C3["silver.fact_shifts, fact_overtime, fact_appointments, waiting_times, cancellations, fact_outcomes"]
        C4["silver.dim_location, dim_skill, dim_service_type, dim_case_complexity"]
    end

    subgraph Gold["Gold - dimensional star schema + marts"]
        D1["gold.dim_employee / dim_employee_governed / dim_client / dim_location / dim_service_type / dim_date"]
        D2["gold.fact_service_requests / fact_appointments / fact_shifts / fact_overtime"]
        D3["gold.mart_daily_demand / mart_weekly_overtime / mart_capacity_utilisation / mart_fairness_workload / mart_service_outcomes / mart_data_quality"]
    end

    subgraph Consume["Consumption"]
        E1["python/features -> model-ready feature tables"]
        E2["python/models -> forecasts, predictions, recommendations"]
        E3["powerbi/data -> Power BI semantic model"]
        E4["governance & monitoring reports"]
    end

    A1 --> B1
    A2 --> B2
    A3 --> B3
    B1 --> C1 --> C3
    B2 --> C2 --> C3
    B3 --> C4
    C1 --> D1
    C2 --> D1
    C3 --> D2
    C4 --> D1
    D1 --> D3
    D2 --> D3
    D3 --> E1 --> E2
    D3 --> E3
    E2 --> E3
    D3 --> E4
    E2 --> E4
```

## Table-level lineage

| Gold table | Built from | Build script |
|---|---|---|
| `gold.dim_employee` | `silver.dim_employee` | `sql/gold/02_star_schema.sql` |
| `gold.dim_employee_governed` | `silver.dim_employee` (protected attributes only) | `sql/gold/02_star_schema.sql` |
| `gold.dim_client` | `silver.dim_client`, filtered on `consent_data_use_flag = true` | `sql/gold/02_star_schema.sql` |
| `gold.fact_service_requests` | `silver.fact_service_requests` + `silver.waiting_times`, orphan client keys excluded | `sql/gold/02_star_schema.sql` |
| `gold.fact_appointments` | `silver.fact_appointments` + `silver.cancellations` + `silver.fact_outcomes` | `sql/gold/02_star_schema.sql` |
| `gold.mart_daily_demand` | `gold.fact_service_requests` | `sql/gold/03_executive_marts.sql` |
| `gold.mart_weekly_overtime` | `gold.fact_overtime` + `gold.dim_employee` | `sql/gold/03_executive_marts.sql` |
| `gold.mart_fairness_workload` | `gold.fact_shifts` + `gold.dim_employee_governed`, small cohorts (`n<8`) suppressed | `sql/gold/03_executive_marts.sql` |
| `gold.mart_data_quality` | Row-level DQ flags raised across every silver table | `sql/gold/04_data_quality_marts.sql` |
| `data/processed/*_features.csv` | Gold marts, joined and feature-engineered | `python/features/feature_engineering.py` |
| `artifacts/monitoring/*` | Feature tables, trained models | `python/models/*`, `python/monitoring/*` |
| `powerbi/data/*.csv` | Gold tables + monitoring artifacts | `python/utils/export_powerbi.py` |

## Reproducing the lineage locally

```bash
python -m python.ingestion.generate_synthetic_data
python -m python.transformation.build_bronze
python -m python.transformation.build_silver
python -m python.transformation.build_gold
python -m python.features.feature_engineering
python -m python.models.train_all
python -m python.utils.export_powerbi
```

or simply `python -m python.run_pipeline --stage all`. The equivalent dbt lineage graph
(`dbt/models/staging -> intermediate -> marts`) mirrors the same transformations for
teams that prefer to operate the silver/gold boundary through dbt rather than raw SQL scripts;
see `dbt/models/*/schema.yml` for the corresponding dbt-native tests.
