# Executive Presentation

*Speaker notes for a 15-20 minute stakeholder briefing. Pairs with the 8-page Power BI report in
`powerbi/Screenshots/` and the 5-minute version in `docs/five_minute_walkthrough.md`.*

## Slide 1 - The problem

"Scheduling across our regions is manual, reactive and inconsistent. We don't see a capacity
shortfall coming -- we discover it the week it happens, as overtime or a growing backlog. Demand
varies by day, season, region and client complexity, but our rostering doesn't yet account for
that variation in advance."

## Slide 2 - What we built

"A workforce capacity and service-demand optimisation platform: it forecasts demand 30 days out,
predicts where we'll run short on capacity, recommends shift changes and skill-matched staff for
open requests, and flags service-level and cancellation risk before it becomes a missed
appointment. Every recommendation goes to a human coordinator for approval -- this is decision
support, not automation."

## Slide 3 - What the data shows today (baseline)

- Show the Executive Overview page. Point to the current overtime, backlog and SLA-met figures.
- "These are the numbers we're benchmarked against. Full detail in `docs/business_case.md`."

## Slide 4 - Demand forecasting

- Show the Demand Forecast page.
- "Our forecasting model cuts prediction error by 18% compared to a naive same-day-last-week
  baseline -- from 23.4% to 19.2% mean absolute percentage error. That's the difference between
  reacting to a surge and planning for it."

## Slide 5 - Capacity and utilisation

- Show the Capacity and Utilisation page.
- "We predict the FTE gap in each region a week ahead, within about 0.07 FTE on average. Right
  now the model shows no region in a material shortfall -- ten of our ten regions show modelled
  surplus capacity, which is itself a useful finding for the budget conversation."

## Slide 6 - Backlog and service levels

- Show the Service Backlog page.
- "Our SLA-breach model reaches 0.94 AUC -- far ahead of predicting breach from urgency alone
  (0.52). The insight: it's regional capacity pressure and case complexity driving breaches, not
  just how urgent a request is tagged. That tells us where to invest."

## Slide 7 - Scheduling recommendations

- Show the Scheduling Recommendations page.
- "The scheduling engine filled 93.5% of open requests in the latest run, using a transparent,
  fairness-aware greedy assignment -- not a black box. Skill-matching gives coordinators a ranked
  shortlist, not a single forced answer."

## Slide 8 - Fairness

- Show the Workforce Fairness page.
- "We test workload and overtime balance across gender and age-band cohorts on every run. Latest
  result: no breach against our 25%/30% gap thresholds. This is a standing control, not a
  one-time check."

## Slide 9 - Outcomes

- Show the Service Outcomes page.
- "Client satisfaction, quality scores and incident rates are tracked alongside operational
  metrics, because a faster schedule that clients aren't happy with isn't actually a win."

## Slide 10 - Governance

- Show the Data Quality and Governance page.
- "Every run checks 7 automated data-quality rules, monitors 3 features for drift, and logs every
  schedule override. This run found a real issue worth acting on: 56% of mandatory safety
  certifications in the sample are expired -- that's exactly the kind of finding this control is
  designed to surface."

## Slide 11 - Business case and ask

- "Targets: 10-20% overtime reduction, 15% backlog reduction, 10% SLA improvement, 20% less
  manual scheduling effort, and better-balanced workloads. Full detail and financial framing in
  `docs/business_case.md`. Ask: approve a 2-region, 6-week shadow-mode pilot per the adoption plan."

## Anticipated questions

- *"Is this replacing our coordinators?"* No -- every output requires human review and approval;
  see `docs/operating_model.md`.
- *"What about client and staff privacy?"* Pseudonymous IDs only, consent-gated client data,
  protected attributes excluded from every model; see `governance/privacy_assessment.md`.
- *"How do we know the models keep working?"* Automated drift and data-quality monitoring on
  every run, with defined retraining criteria; see `governance/model_card.md`.
