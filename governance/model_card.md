# Model Card: Workforce Capacity and Service-Demand AI Components

This model card covers the six trained/predictive models and four deterministic
decision-support components in `python/models/`. Metrics below are the actual output of the
most recent full pipeline run (`artifacts/models/registry.json`,
`artifacts/monitoring/model_run_summary.json`) against the synthetic dataset described in
`governance/data_catalogue.md` -- regenerate with `python -m python.run_pipeline --stage all`
to reproduce them.

## Intended use

Decision support for workforce planning and scheduling coordinators. No component in this
platform takes an automated action on a client's appointment or an employee's roster without a
human review step (see `docs/operating_model.md` "Human-in-the-loop control points"). Not
intended for use in employment decisions (hiring, termination, discipline) or as a clinical
decision tool.

## Models

### 1. Service-demand forecasting (`demand_forecasting.py`)
- **Task**: predict daily organisation-wide service-request volume, allocated to regions by
  trailing share.
- **Baseline**: seasonal-naive (last-week-same-weekday). **Challenger**: HistGradientBoostingRegressor.
- **Result**: baseline MAPE 23.4%, challenger MAPE 19.2% (MAE 3.77 requests/day, RMSE 4.74) --
  an 18.0% improvement over baseline on a 42-day rolling-origin holdout. **Status: warning**
  (threshold: warn ≥18% MAPE, breach ≥25%) -- close to the healthy band; the largest remaining
  error is around the calendar edges of the organic demand-growth trend the generator applies
  across the year (see the drift finding below, which flags the same trend independently).

### 2. Request-complexity prediction (`complexity_prediction.py`)
- **Task**: predict a request's complexity tier (Low/Medium/High/Critical) at intake, from
  request metadata only -- no client history or protected attributes.
- **Baseline**: majority-class. **Challenger**: HistGradientBoostingClassifier.
- **Result**: baseline macro F1 0.13, challenger macro F1 0.40 (accuracy 44.4%, roughly 3x the
  baseline). **Status: healthy** against a deliberately recalibrated threshold (warn <0.38, breach
  <0.28) -- see "Known limitations" below for why this ceiling is realistic for the problem as
  framed.

### 3. Cancellation / no-show prediction (`cancellation_prediction.py`)
- **Task**: predict whether a scheduled appointment will be cancelled or result in a no-show.
- **Baseline**: class-weighted logistic regression. **Challenger**: HistGradientBoostingClassifier.
- **Result**: baseline ROC-AUC 0.55, challenger ROC-AUC 0.66 (PR-AUC 0.44 against a 30.6% positive
  rate). **Status: warning** (threshold: warn <0.68, breach <0.60). This is an honest result: the
  signal available at scheduling time (service type, travel time, urgency, calendar, wait time) is
  real and clearly above baseline, but modest in absolute terms, and the model is flagged for
  human review of any high-confidence prediction rather than automated action, consistent with
  its "warning" status.

### 4. Service-level (SLA) breach prediction (`service_level_breach_prediction.py`)
- **Task**: predict whether a request will breach its response-time SLA target.
- **Baseline**: logistic regression on urgency alone. **Challenger**: HistGradientBoostingClassifier.
- **Result**: baseline ROC-AUC 0.52, challenger ROC-AUC 0.94 -- urgency alone is close to
  uninformative on its own, but adding regional capacity pressure and case complexity produces a
  strong model. At the operating threshold (0.35), precision is 0.44 and recall is 0.84
  (deliberately recall-weighted, since a missed at-risk request is more costly than a false alarm
  a coordinator can quickly dismiss). **Status: healthy**.

### 5. Workload estimation (`workload_estimation.py`)
- **Task**: predict a region's total actual hours worked next week from forecast demand,
  complexity mix and current contracted capacity.
- **Baseline**: linear regression on contracted hours alone. **Challenger**: HistGradientBoostingRegressor.
- **Result**: baseline MAE 26.7 hours (MAPE 11.9%), challenger MAE 18.4 hours (MAPE 7.7%).
  **Status: healthy**.

### 6. Capacity-gap prediction (`capacity_gap_prediction.py`)
- **Task**: predict the FTE shortfall/surplus for a region next week.
- **Baseline**: mean predictor (MAE 2.13 FTE). **Challenger**: HistGradientBoostingRegressor
  (MAE 0.07 FTE). **Status: healthy**. Current snapshot (trailing 4-week average): see
  `artifacts/monitoring/model_run_summary.json` -- in the most recent run no region showed a
  material shortfall (mean modelled gap approximately -6.6 FTE, i.e. an organisation-wide surplus),
  consistent with the shift-recommendation output below.

## Decision-support components (not statistical models)

| Component | What it does | Latest run result |
|---|---|---|
| Skill matching | Ranks eligible employees for open backlog requests by skill fit, proficiency, workload balance and location match | 60 open requests scored, average top-match score 0.82 |
| Scheduling optimiser | Greedy, fairness-aware assignment of open requests to available skill-eligible staff | 93.5% fill rate (415/444), workload Gini coefficient 0.30, 108/108 active employees utilised |
| Shift recommendation | Translates the capacity-gap prediction into a bounded recommended shift-count change per region | Most recent week: 0 regions needing more capacity, 10 with a modelled surplus |
| Scenario planning | Closed-form what-if simulator over demand growth / staffing change assumptions | 5 scenarios generated (baseline, winter surge, staffing uplift, combined, budget freeze) |

## Explainability

`complexity_prediction.py` and `cancellation_prediction.py` report HistGradientBoosting native
feature importances where available. `service_level_breach_prediction.py`'s strong lift over the
urgency-only baseline is itself an explainability finding: it shows that regional capacity
pressure and case complexity -- not urgency alone -- drive breach risk, which is a directly
actionable insight for capacity planning (see `docs/business_case.md`). The scheduling optimiser
and skill-matching component are deliberately rule-based and fully transparent rather than
learned, so a coordinator can always trace why a specific candidate was ranked first.

## Bias / fairness assessment

`python/governance/fairness_checks.py` compares workload (hours per shift) and overtime incidence
across gender and age-band cohorts -- attributes that are never used as model features (see
`governance/privacy_assessment.md`). Latest run: **no cohort breach** against the configured
25%/30% gap thresholds (`configs/monitoring.yml`); full cohort breakdown in
`artifacts/monitoring/fairness_report.json`. Cohorts below 8 employees are suppressed at both the
gold-mart and governance-check layer.

## Drift monitoring

`python/monitoring/model_monitoring.py` computes PSI on the demand-forecast feature set between
the first and second half of the synthetic history. Latest run shows `requests` and
`rolling_mean_7` in PSI breach (0.35 and 1.46 respectively) -- this is expected and intentional:
the generator applies an 18% organic demand-growth trend across the year, and the drift monitor
correctly flags it. `avg_complexity_score` shows only mild ("warning") drift. Because 2+ features
are in breach, the retraining trigger in `configs/monitoring.yml` fires
(`retraining_recommended: true`), which is the intended behaviour of the control, not a defect.

## Thresholds and alerts

All thresholds live in `configs/monitoring.yml` (`model_thresholds`, `fairness_thresholds`,
`model_monitoring`) so they can be reviewed and versioned independently of code.

## Human review and override tracking

Every model output is advisory. `python/governance/audit_log.py` summarises the
`override_flag`/`override_reason` already captured on `gold.fact_appointments` -- latest run: a
4.9% override rate across 6,906 appointments, with "Urgent reassignment", "Skill match
unavailable" and "Client preference" the three leading reasons. This audit record is appended
(not overwritten) on every pipeline run, forming an immutable trail.

## Model registry

`python/models/model_registry.py` writes every model's metrics, threshold status and notes to
`artifacts/models/registry.json` on each run, replacing only that model's prior entry -- a
lightweight stand-in for a Fabric/MLflow model registry.

## Retraining criteria

> Breach threshold sustained for 2 consecutive monitoring cycles OR PSI breach on 2+ features.

(`configs/monitoring.yml: model_monitoring.retraining_trigger`)

## Known limitations

1. **Complexity-tier prediction** is fundamentally constrained by problem framing: complexity
   tier is a client-level attribute, and this model predicts it from request-level intake
   metadata only, deliberately excluding case history to avoid circularity (if we already stored
   a client's tier from a prior assessment, "predicting" it would not be a genuine intake-time
   problem). The recalibrated threshold in `configs/monitoring.yml` reflects that honestly rather
   than inflating the apparent ceiling. Roadmap: add consented, privacy-reviewed prior-visit
   summary features to lift this further.
2. **Cancellation prediction** is in "warning" status by design of the underlying process: many
   cancellations in a real service organisation are driven by client-side events (illness,
   changed plans) that are not observable in scheduling data. The model is explicitly a triage
   aid, not a gate.
3. **Synthetic data** approximates but does not replace real operational history. Before a
   production go-live, all thresholds in `configs/monitoring.yml` should be re-validated against
   real historical performance.

## Review cadence

Reviewed at every model or feature change, and at minimum quarterly by the Model Risk Reviewer
role defined in `governance/access_control_matrix.md`.
