# End-User Walkthrough

A short, persona-based tour of the report for someone opening it for the first time.

## If you are a Regional Coordinator

Start on **Scheduling Recommendations**. The KPI row tells you this cycle's fill rate and how
many requests still need a manual match. The main table ranks candidates for each open request by
skill fit, workload balance and location -- pick the top row unless you have a reason not to
(and if you do override it, note the reason; it is logged automatically). Check **Service
Backlog** next to see which urgency tiers are building up in your region, and **Capacity and
Utilisation** to see whether you're modelled short or long on hours next week.

## If you are a Workforce Planning Lead

Start on **Demand Forecast**. The 30-day line shows where volume is heading and the model-status
chip tells you whether to trust it at face value this cycle. Move to **Capacity and Utilisation**
to see the FTE gap this implies by region, then **Workforce Executive Overview** for the
organisation-wide scorecard against the four target KPIs in `docs/business_case.md`.

## If you are a People & Culture Lead

Go straight to **Workforce Fairness**. The heatmap shows every monitored dimension (gender, age
band, role, region, employment type) and whether its workload/overtime gap is within threshold,
approaching it, or a genuine breach. Cohorts too small to report on safely are marked
"Suppressed", not silently dropped.

## If you are a Model Risk Reviewer or Data Platform Engineer

Go to **Data Quality and Governance**. The rule table shows exactly which of the 7 automated
checks passed, and the model-status bar shows which of the 6 trained models are healthy, in
warning, or in breach this cycle. Both link back to `governance/model_card.md` and
`governance/data_quality_rules.yml` for the full definition of each check.

## If you are an executive or seeing this for the first time

**Workforce Executive Overview** is built to be read in under a minute: four KPIs against target,
one trend, one regional comparison, and a plain-English "what this means" card. Everything else
in the report is the detail behind that one page.

## A note on what you're looking at

These are reproducible, script-rendered design mockups (`powerbi/Templates/render_mockups.py`),
not a native Power BI file export -- they exist to demonstrate the intended page layout,
navigation, KPI design, chart choices, legends, tooltips, cross-filtering and narrative structure
precisely and reproducibly. The semantic model, DAX measures and sample data needed to build the
live report are in `powerbi/semantic_model.md`, `powerbi/dax_measures.md` and `powerbi/data/`.
