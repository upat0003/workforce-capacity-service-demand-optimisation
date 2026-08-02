# Power BI Dashboard Specification

Eight pages, each following the same interaction contract: a colour-coded legend under every
chart, labelled axes, a hover-tooltip callout anchored to one data point, a cross-filter
highlight (an outlined selected mark), and a persistent, removable filter-chip row in place of a
static date label. Palette: `powerbi/theme.json` (teal-green primary, coral/salmon accent).
Reproducible mockups are rendered by `powerbi/Templates/render_mockups.py` from
`powerbi/Templates/pages.json` into `powerbi/Screenshots/` (clean) and `powerbi/Mockups/`
(numbered-callout annotated versions).

## 1. Workforce Executive Overview

- **Audience**: Service Delivery Executive, Workforce Planning Lead.
- **KPIs**: overtime hours (trailing 4 weeks), backlog requests, SLA-met rate, workforce
  utilisation.
- **Visuals**: (1) trailing 12-week trend of overtime hours vs. target band; (2) regional
  comparison of SLA-met rate; (3) top regions by backlog volume.
- **Drill-through**: any region bar drills to Capacity and Utilisation, filtered to that region.
- **Alert threshold**: overtime hours trending above the 20%-reduction target line turns the KPI
  tile amber; backlog above baseline turns it red.
- **Narrative**: headline read of whether the organisation is currently ahead of or behind its
  four target KPIs.

## 2. Demand Forecast

- **Audience**: Workforce Planning Lead.
- **KPIs**: 30-day forecast total requests, forecast MAPE, model status, seasonal uplift %.
- **Visuals**: (1) historical + 30-day forecast line with confidence shading; (2) forecast by
  region (top 5 bar).
- **Drill-through**: region bar drills to that region's own demand trend.
- **Alert threshold**: MAPE ≥18% shows a "Warning" model-status chip; ≥25% shows "Breach"
  (`configs/monitoring.yml`).
- **Narrative**: which regions are expected to see the largest demand increase next month and
  why (seasonal winter uplift, organic growth trend).

## 3. Capacity and Utilisation

- **Audience**: Workforce Planning Lead, Regional Coordinator.
- **KPIs**: capacity-gap FTE (org-wide), utilisation %, regions in shortfall, regions in surplus.
- **Visuals**: (1) utilisation heatmap by region x week; (2) capacity-gap FTE by region (diverging
  bar, shortfall vs. surplus).
- **Drill-through**: heatmap cell drills to Scheduling Recommendations for that region/week.
- **Alert threshold**: utilisation outside the 78-92% target band highlighted.
- **Narrative**: where capacity is tight vs. where there's modelled headroom to redeploy from.

## 4. Service Backlog

- **Audience**: Service Delivery Executive, Regional Coordinator.
- **KPIs**: open backlog count, average backlog age, SLA breach rate, requests at risk (model
  flag).
- **Visuals**: (1) backlog by urgency and region (stacked bar); (2) SLA-met trend over time.
- **Drill-through**: bar segment drills to the underlying request list (table page).
- **Alert threshold**: backlog age >7 days flips to red; SLA-breach-risk flag >0.35 probability
  highlighted per `python/models/service_level_breach_prediction.py`.
- **Narrative**: which regions/urgency combinations are driving the backlog, and how many are
  flagged at-risk before they breach.

## 5. Scheduling Recommendations

- **Audience**: Regional Coordinator.
- **KPIs**: fill rate %, workload Gini, requests unassigned, avg skill-match score.
- **Visuals**: (1) recommended shift-count change by region (diverging bar); (2) ranked
  skill-match candidate table for a selected open request.
- **Drill-through**: region bar drills to that region's shift-recommendation detail.
- **Alert threshold**: fill rate <90% highlighted amber.
- **Narrative**: this week's concrete, actionable scheduling suggestions and top candidate
  matches, ready for coordinator sign-off.

## 6. Workforce Fairness

- **Audience**: People & Culture Lead, Model Risk Reviewer.
- **KPIs**: workload gap % (gender), overtime gap % (age band), cohorts suppressed, any-breach flag.
- **Visuals**: (1) cohort gap heatmap (dimension x gap type); (2) hours-per-shift by cohort (donut/bar).
- **Drill-through**: none (aggregate-only by design; see privacy_assessment.md small-cohort rule).
- **Alert threshold**: gap >25% (workload) or >30% (overtime) flips to breach red.
- **Narrative**: whether workload and overtime are currently balanced across governed employee
  cohorts, and which cohort (if any) needs review.

## 7. Service Outcomes

- **Audience**: Quality & Safety Lead, Service Delivery Executive.
- **KPIs**: avg satisfaction, avg quality score, incident rate, cancellation rate.
- **Visuals**: (1) satisfaction and quality trend by month; (2) cancellation reasons (donut).
- **Drill-through**: cancellation-reason segment drills to the cancellation detail table.
- **Alert threshold**: satisfaction <3.8 or incident rate >2.5% highlighted.
- **Narrative**: whether faster, better-matched scheduling is translating into better client
  outcomes, not just better operational metrics.

## 8. Data Quality and Governance

- **Audience**: Data Platform Engineer, Model Risk Reviewer.
- **KPIs**: DQ pass rate %, models in breach, drifted features, override rate %.
- **Visuals**: (1) data-quality rule pass/fail table; (2) model threshold status by model (bar).
- **Drill-through**: a failing rule drills to the affected dataset's row-level detail (table page).
- **Alert threshold**: any rule <97% pass rate, or any model in "breach" status.
- **Narrative**: whether the platform's own controls are green, and what to action if not --
  this run's real finding is the expired-certification rule failing at 43.7% pass rate.

## Mobile layout note

Scheduling Recommendations and Service Backlog are designed to collapse to a single-column
mobile layout first (KPI tiles stacked, primary visual full-width, secondary visual and narrative
card below), since regional coordinators are the most likely persona to check the report from a
phone between visits.

## Cross-page consistency

- Filter chips (Period, Region, Model version) persist across every page and are shown top-right.
- Every chart has a legend directly beneath it, labelled axes, and one tooltip callout on the
  most relevant data point (the latest period, the highlighted region, or the top-ranked row).
- Cross-filter highlighting is shown as an outlined bar/cell/row on the primary chart of each page.
