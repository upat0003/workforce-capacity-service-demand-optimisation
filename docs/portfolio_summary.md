# Portfolio Summary

## One-line summary

An end-to-end workforce capacity and service-demand optimisation platform -- synthetic data,
medallion data architecture, ten AI/decision-support components, and an 8-page Power BI report --
built to demonstrate senior data/AI/analytics practice for people-operations and service-delivery
organisations, with governance and responsible-AI controls throughout.

## Why this project

Melbourne and Victorian service organisations (community services, field services, councils,
health-adjacent providers) face a common, under-solved problem: aligning workforce capacity to
variable service demand while keeping workloads fair and service levels intact. This project
builds a realistic, defensible solution to that problem end to end, rather than a single notebook
or a single dashboard.

## What's inside

- **Data**: 17 realistic synthetic datasets (~54,000 rows) with deliberate data-quality issues --
  duplicates, orphaned keys, missing values, expired certifications, casing inconsistencies.
- **Data engineering**: bronze/silver/gold medallion architecture in DuckDB, mirrored in a dbt
  project, with 7 automated data-quality rules.
- **AI/ML**: 6 trained models (demand forecasting, complexity prediction, cancellation
  prediction, SLA-breach prediction, workload estimation, capacity-gap prediction) each with a
  real baseline and challenger, plus 4 deterministic decision-support components (skill matching,
  a constrained greedy scheduling optimiser, shift recommendations, scenario planning).
- **Governance**: data catalogue, lineage, privacy assessment, access-control matrix, risk
  register, model card, fairness checks, drift monitoring and an override audit trail -- all
  runnable, not just documented.
- **BI**: an 8-page Power BI semantic model, DAX measure library and reproducibly-rendered
  dashboard mockups with a consistent teal/coral visual language and full interaction design
  (legends, tooltips, cross-filtering, filter chips).
- **Engineering**: modular Python package, pytest test suite, GitHub Actions CI, Docker Compose,
  config-driven thresholds, structured logging.

## Representative results (from the latest pipeline run)

| Result | Value |
|---|---|
| Demand-forecast accuracy improvement over seasonal-naive baseline | 18% (MAPE 23.4% → 19.2%) |
| SLA-breach prediction, urgency-only baseline vs. full model | ROC-AUC 0.52 → 0.94 |
| Complexity-tier prediction, majority-class baseline vs. challenger | macro F1 0.13 → 0.40 |
| Scheduling optimiser fill rate | 93.5% of open backlog requests assigned |
| Workforce fairness check | No cohort breach against 25%/30% gap thresholds |
| Data-quality rules passing | 6 of 7 (one genuine finding: 56% of a certification sample expired) |
| Full pipeline runtime | ~15 seconds end to end on a modest laptop |

## Resume-ready bullet points

- Designed and built an end-to-end workforce capacity and service-demand optimisation platform
  covering synthetic data generation, a medallion (bronze/silver/gold) data architecture, ten
  AI/ML and decision-support components, and an 8-page Power BI reporting layer.
- Trained and evaluated six machine-learning models (gradient-boosted regression and
  classification) for demand forecasting, complexity triage, cancellation risk, SLA-breach risk,
  workload estimation and capacity-gap prediction, each benchmarked against a transparent
  baseline with real computed metrics (e.g. lifted SLA-breach prediction from 0.52 to 0.94 ROC-AUC
  by identifying regional capacity pressure and case complexity as the true drivers over urgency alone).
- Built a constrained greedy scheduling optimiser and skill-matching engine achieving a 93.5%
  fill rate on open service requests while actively balancing workload across staff.
- Implemented a responsible-AI governance layer: automated data-quality rules, fairness checks
  across protected employee cohorts with small-cohort suppression, model drift monitoring,
  role-based access control testing, and an immutable schedule-override audit trail.
- Authored a full documentation suite -- business case, architecture, data dictionary, metrics
  catalogue, model card, risk register, privacy assessment -- to a standard suitable for
  stakeholder and audit review.
- Designed an 8-page Power BI semantic model and DAX measure library, with a reproducible,
  script-rendered dashboard mockup pipeline (Python/Pillow) implementing a full interaction
  contract (legends, axis labels, hover tooltips, cross-filter highlighting, filter chips).
- Set up CI/CD (GitHub Actions), Docker Compose, and a pytest suite covering data quality, model
  training and governance logic, with all thresholds externalised to versioned configuration.

## Where to look first

- [`README.md`](../README.md) -- overview and quick start
- [`docs/business_case.md`](business_case.md) -- the "why"
- [`governance/model_card.md`](../governance/model_card.md) -- the AI layer, with real metrics
- [`powerbi/Screenshots/`](../powerbi/Screenshots/) -- the 8 dashboard pages
- [`docs/five_minute_walkthrough.md`](five_minute_walkthrough.md) -- a guided tour
