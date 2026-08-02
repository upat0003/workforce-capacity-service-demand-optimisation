# Metrics Catalogue

Every metric shown on a Power BI dashboard page, with its definition, calculation, owner and
alert threshold. Values in the "latest run" column reflect the most recent
`python -m python.run_pipeline --stage all` execution and are reproducible from
`artifacts/monitoring/` and `powerbi/data/`.

| Metric | Definition | Calculation | Owner | Threshold | Dashboard page |
|---|---|---|---|---|---|
| Weekly overtime hours | Total overtime hours worked across the organisation in a week | `sum(overtime_hours)` from `gold.mart_weekly_overtime` | Workforce Planning | Target: 10-20% reduction vs. baseline | Executive Overview, Capacity and Utilisation |
| Overtime rate % | Overtime hours as a share of total hours worked | `overtime_hours / actual_hours_worked` | Workforce Planning | Warn >15%, breach >25% | Capacity and Utilisation |
| Open backlog requests | Service requests with no scheduled appointment | `count(*) WHERE status = 'Backlog'` from `gold.fact_service_requests` | Service Delivery | Target: 15% reduction vs. baseline | Service Backlog |
| Average backlog age (days) | Average days a backlog request has been open | `avg(datediff('day', requested_date, today))` | Service Delivery | Warn >7 days | Service Backlog |
| SLA-met rate % | Share of requests scheduled within their SLA target | `avg(sla_met_flag)` from `gold.fact_service_requests` | Service Delivery | Target: 10% improvement vs. baseline | Executive Overview, Service Outcomes |
| Demand forecast MAPE | Mean absolute percentage error of the 30-day demand forecast | See `python/models/demand_forecasting.py` | Data Platform / Model Risk | Warn ≥18%, breach ≥25% | Demand Forecast |
| Capacity gap (FTE) | Modelled shortfall/surplus of FTE vs. forecast demand, by region | `python/models/capacity_gap_prediction.py` | Workforce Planning | Warn MAE ≥1.5 FTE, breach ≥2.5 FTE | Capacity and Utilisation, Demand Forecast |
| Workforce utilisation % | Actual hours worked / rostered capacity hours | `gold.mart_capacity_utilisation` | Workforce Planning | Target band 78-92% | Capacity and Utilisation |
| Scheduling fill rate % | Share of open requests successfully assigned by the scheduling optimiser | `python/models/scheduling_optimiser.py` | Regional Coordinator | Target ≥90% | Scheduling Recommendations |
| Skill-match score | Weighted fit score (skill, proficiency, workload balance, location) for a recommended candidate | `python/models/skill_matching.py` | Regional Coordinator | Informational | Scheduling Recommendations |
| Workload Gini coefficient | Inequality measure of rostered/assigned hours across staff (0 = perfectly equal) | `python/models/scheduling_optimiser.py` | People & Culture | Target ≤0.20 | Workforce Fairness |
| Workload gap % (by cohort) | Gap in average hours per shift between the highest and lowest governed cohort | `python/governance/fairness_checks.py` | People & Culture | Breach >25% | Workforce Fairness |
| Overtime gap % (by cohort) | Gap in overtime incidence between the highest and lowest governed cohort | `python/governance/fairness_checks.py` | People & Culture | Breach >30% | Workforce Fairness |
| Cancellation rate % | Share of appointments cancelled or resulting in a no-show | `gold.fact_appointments.status` | Service Delivery | Informational; model AUC tracked separately | Service Outcomes |
| Client satisfaction score | Average client-reported satisfaction (1-5) | `avg(client_satisfaction_score)` from `gold.fact_appointments` | Quality & Safety | Warn <3.8 | Service Outcomes |
| Incident rate % | Share of completed appointments with a recorded incident | `avg(incident_flag)` | Quality & Safety | Breach >2.5% | Service Outcomes |
| Data-quality pass rate % | Share of automated DQ rules passing | `python/monitoring/data_quality_monitoring.py` | Data Platform Engineer | Breach <97% | Data Quality and Governance |
| Feature drift PSI | Population stability index on key forecast features | `python/monitoring/model_monitoring.py` | Model Risk Reviewer | Warn ≥0.10, breach ≥0.25 | Data Quality and Governance |
| Override rate % | Share of appointments where a coordinator overrode the system-recommended match | `python/governance/audit_log.py` | Regional Coordinator / Model Risk | Informational; reasons reviewed monthly | Data Quality and Governance, Scheduling Recommendations |
| Access control test pass rate | Share of the sample access-control test suite resolving to the expected allow/deny outcome | `python/governance/access_control.py` | Model Risk Reviewer | Breach: any unexpected allow | Data Quality and Governance |

## Baseline reference

Baseline values used for target-tracking are frozen at the point a model or dashboard is first
put into production and stored alongside the relevant config (`configs/monitoring.yml` for model
thresholds, `docs/business_case.md` for business KPI baselines). They are not silently
recalculated on every run, so an improvement is always measured against a fixed point in time.
