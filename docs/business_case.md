# Business Case

## Executive problem statement

Scheduling across the organisation's regional and community service footprint is a largely
manual, spreadsheet- and phone-driven process. Demand varies materially by day of week, season,
region and client complexity, but rostering decisions are made reactively, week to week, with no
forward visibility into where capacity will fall short. The consequences are consistent and
measurable in the data behind this platform: overtime concentrated in a handful of regions and
staff, a persistent service-request backlog, inconsistent service-level performance, and
workloads that are not evenly distributed across the workforce.

## Stakeholder personas

| Persona | Primary concern | What this platform gives them |
|---|---|---|
| Regional Coordinator | Filling tomorrow's roster without breaching hours limits | Shift recommendations, skill-matched candidate lists, capacity-gap alerts |
| Workforce Planning Lead | Forward visibility into demand and staffing needs | 30-day demand forecast, capacity-gap prediction, scenario planner |
| People & Culture Lead | Fair, sustainable workloads and overtime exposure | Workforce Fairness dashboard, workload Gini coefficient, overtime gap reporting |
| Service Delivery Executive | Whether service levels and backlog are under control | Executive Overview and Service Backlog dashboard pages |
| Model Risk / Governance Reviewer | Whether the AI components are safe, fair and monitored | Model card, fairness checks, drift monitoring, override audit trail |
| Client (indirect) | Being seen within a reasonable time by an appropriately skilled worker | Reduced wait times, better skill-matched appointments, fewer cancellations |

## Current-state pain points

1. Overtime is reactive: shortfalls are discovered the week they happen, not forecast ahead of time.
2. The service-request backlog grows unevenly across regions with no shared visibility.
3. Scheduling is manual and time-consuming, with skill-matching done from memory or informal notes.
4. There is no systematic check on whether workload and overtime are distributed fairly across staff.
5. Service-level performance is reported after the fact, not predicted and pre-empted.

## Target-state operating model

A forecast-led planning cycle: weekly demand and capacity-gap forecasts inform shift
recommendations a coordinator reviews and approves; skill-matching and a constrained scheduling
heuristic reduce manual effort; fairness and data-quality controls run automatically on every
cycle; scenario planning supports budget and headcount conversations ahead of time rather than
after a backlog has already formed. See [`docs/operating_model.md`](operating_model.md) for the
detailed process design.

## Baseline and target KPIs

Baselines are computed directly from the synthetic operating history (see
`artifacts/monitoring/model_run_summary.json` and `powerbi/data/*` for the live computed figures
from the most recent pipeline run). Targets are the business outcomes this solution is designed
to support.

| KPI | Baseline (synthetic history) | Target | Rationale |
|---|---|---|---|
| Weekly overtime hours | Trailing 12-week average, `gold.mart_weekly_overtime` | 10-20% reduction | Better demand visibility reduces reactive overtime |
| Open backlog requests | Current count, `gold.fact_service_requests` status = Backlog | 15% reduction | Forecast-led scheduling and prioritisation clear backlog faster |
| SLA-met rate | `gold.fact_service_requests.sla_met_flag` | 10% improvement | Breach prediction lets coordinators intervene before an SLA is missed |
| Manual scheduling effort (proxy: coordinator time per week) | Estimated from current fully-manual process | 20% reduction | Skill-matching and the scheduling optimiser remove first-pass manual matching |
| Workload balance (Gini coefficient of rostered hours) | `python/models/scheduling_optimiser.py` output | ≤ 0.20 | Fairness-aware assignment logic |
| Median client wait time (request to appointment) | `gold.fact_service_requests.waiting_days_to_schedule` | 12% reduction | Faster, better-prioritised scheduling |
| Workforce utilisation | `gold.mart_capacity_utilisation` | 78-92% band | Neither under- nor over-utilised |

## Estimated financial and operational value

Illustrative, order-of-magnitude estimates based on the synthetic organisation's scale (~150
employees, ~7,000 service requests/year) -- presented as the kind of business case a workforce
planning lead would take to a budget conversation, not as an audited forecast:

| Value driver | Estimate | Basis |
|---|---|---|
| Overtime cost avoidance | ~10-20% of current overtime spend | Applying the overtime-reduction target to the trailing overtime-hours baseline at the organisation's blended hourly rate |
| Coordinator time released | ~4-6 hours/week per regional coordinator | 20% reduction in manual scheduling effort across ~10 regions |
| Backlog-driven escalation/complaint cost avoidance | Reduced by the same proportion as backlog reduction (15%) | Fewer aged, unresolved requests reduce complaint and re-work volume |
| Missed-SLA remediation cost avoidance | Reduced by the same proportion as the SLA improvement target (10%) | Fewer expedited/urgent re-bookings required after a breach |

## Risks and limitations

See [`governance/risk_register.md`](../governance/risk_register.md) for the full register. The
headline limitations to be transparent about: the complexity-tier and workload-estimation models
show real, honestly-reported constraints given the intake-time features available (see
[`governance/model_card.md`](../governance/model_card.md)); synthetic data approximates but does
not replace validation against real operational history before a production go-live.

## Adoption plan

1. **Pilot** in 2 regions for 6 weeks, shadow-mode (recommendations shown, not auto-applied).
2. **Coordinator training** on shift recommendations, skill-matching and override workflow.
3. **Controlled rollout** to all regions with weekly model-monitoring review for the first
   quarter.
4. **Steady state**: monthly governance review (data quality, fairness, drift) per the cadence in
   `governance/model_card.md`.
