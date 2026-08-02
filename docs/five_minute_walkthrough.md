# Five-Minute Walkthrough Script

*Use this for a quick portfolio demo or interview screen-share. Assumes the Power BI screenshots
in `powerbi/Screenshots/` are open, or a live report built from `powerbi/data/`.*

**0:00-0:30 -- Frame the problem**
"This is a workforce capacity and service-demand optimisation platform for a multi-region field
and community services organisation. The core problem: scheduling is manual and reactive, so
overtime, backlog and service levels all suffer. I built the full stack -- synthetic data,
medallion pipeline, ten AI/decision-support components, and an 8-page Power BI report -- to solve
it end to end."

**0:30-1:15 -- Data and architecture**
"Everything starts from a synthetic but realistic year of operating history: 150 employees, 520
clients, ~7,300 service requests, 17,000 shifts, deliberately including data-quality issues --
duplicate records, orphaned foreign keys, expired certifications, missing values -- so the
pipeline has real work to do. It flows through a bronze/silver/gold medallion architecture in
DuckDB, mirrored in a dbt project, designed to map directly onto Microsoft Fabric." (Show
`docs/architecture.md` diagram.)

**1:15-2:30 -- The AI layer**
"Ten components: demand forecasting, complexity prediction, cancellation prediction, SLA-breach
prediction, workload estimation, capacity-gap prediction, skill matching, a greedy scheduling
optimiser, shift recommendations and scenario planning. Every model has a real baseline and a
real challenger, trained on this data just now -- for example, the SLA-breach model goes from
0.52 AUC using urgency alone to 0.94 AUC once regional capacity pressure and complexity are
added. That's a genuine, explainable finding, not a headline number." (Show
`governance/model_card.md`.)

**2:30-3:45 -- Governance**
"Nothing here runs unchecked. Every pipeline run executes data-quality rules, fairness checks
across protected employee cohorts, an access-control test, and drift monitoring -- and logs every
scheduling override. In the latest run, the data-quality control actually caught something real:
56% of mandatory safety certifications are expired in the sample. That's the control working as
intended." (Show `powerbi/Screenshots/08_data_quality_and_governance.png`.)

**3:45-4:45 -- Power BI**
"Eight pages: Executive Overview, Demand Forecast, Capacity and Utilisation, Service Backlog,
Scheduling Recommendations, Workforce Fairness, Service Outcomes, and Data Quality and
Governance. Every page follows the same interaction pattern -- legends, labelled axes, a hover
tooltip, a cross-filter highlight, and removable filter chips -- so it reads as one coherent
product, not eight disconnected charts." (Flip through 2-3 pages.)

**4:45-5:00 -- Close**
"Full documentation -- business case, data dictionary, model card, risk register, DAX measures --
is all in the repo. Happy to go deeper on any layer: the data generation, the modelling choices,
or the governance design."
