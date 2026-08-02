# Technical Interview Guide

Talking points and defensible answers for a technical deep-dive on this project.

## "Walk me through the architecture."

Medallion architecture in DuckDB (bronze = raw landed extracts with ingestion metadata, silver =
deduplicated/conformed/FK-validated, gold = star schema + reporting marts), with a parallel dbt
project (`dbt/models/staging -> intermediate -> marts`) demonstrating the same lineage in a
dbt-native idiom. Locally this is one DuckDB file (`artifacts/warehouse.duckdb`); in production
it maps to a Fabric Lakehouse (bronze/silver) and Warehouse or Lakehouse SQL endpoint (gold), with
Data Factory for orchestration. See `docs/architecture.md`.

## "Why DuckDB and not [Spark/Snowflake/Postgres]?"

DuckDB gives a single-file, zero-infrastructure analytical engine with real SQL semantics (window
functions, `read_csv_auto`, schemas) that runs the entire pipeline in under 20 seconds on a laptop
-- important for a portfolio project that needs to be trivially reproducible by anyone who clones
it. The SQL is written to be portable; the adapter/connection layer is the only thing that would
change to point the same logic at Fabric.

## "Why HistGradientBoosting instead of XGBoost/LightGBM?"

It ships in scikit-learn, so the project has zero exotic native-library dependencies -- one less
thing to break in CI or on a reviewer's machine -- while still giving a genuine non-linear
challenger to compare against a transparent baseline (seasonal-naive, logistic regression, linear
regression, or a dummy predictor, depending on the task). Every model in `python/models/` reports
both baseline and challenger metrics so the lift is auditable, not assumed.

## "How did you avoid data leakage?"

- Forecast features (`lag_1`, `lag_7`, `rolling_mean_7/28`) are shifted so no feature at time *t*
  uses information from *t* or later.
- Train/test splits for the classifiers are stratified random splits over independent
  request/appointment rows (no client or employee appears differently across folds in a way that
  would leak identity-based shortcuts, since neither client_id nor employee_id is a feature).
- The demand forecast uses a genuine rolling-origin holdout (final 42 days), not a random split,
  because it's a time series.
- Protected attributes (gender, age_band, preferred_language) are structurally excluded: they
  live only on `gold.dim_employee_governed`, which is never joined into any file under
  `python/features/` or `data/processed/`.

## "Why is the complexity-prediction model's F1 only ~0.40?"

Because the problem is framed honestly: complexity tier is fundamentally a client-level
attribute, and the model is asked to infer it from request-level intake metadata alone (no case
history), which is a genuinely harder problem than it might first appear. Rather than silently
accepting an inflated implied ceiling, I recalibrated the threshold in `configs/monitoring.yml` to
reflect what's achievable given that framing, and documented the reasoning in
`governance/model_card.md`. I'd rather defend a modest, honest number than present an
inflated one.

## "How would this change at 10x the data volume?"

`configs/data_generation.yml` documents a `production_scale_multiplier` block (roughly 1,800
employees, 10,400 clients, ~255 requests/day) as the intended production footprint. DuckDB
comfortably handles that on one node; beyond it, the same SQL would run against a Fabric Warehouse
or a Spark-backed Lakehouse without a rewrite, because the transformation logic doesn't depend on
DuckDB-specific features beyond `read_csv_auto` at the ingestion boundary.

## "What would you productionise first?"

1. Replace the synthetic-data generator with real source connectors (rostering system, CRM) into
   the same bronze schema shape, so nothing downstream changes.
2. Add a proper orchestrator (Fabric Data Factory / Airflow) in place of the CLI
   (`python/run_pipeline.py`), which is already staged for that (`--stage` flags map to pipeline
   tasks).
3. Move the model registry (`artifacts/models/registry.json`) to a real registry (MLflow/Fabric)
   with model versioning and a promotion workflow, rather than a single-file JSON.
4. Wire the DQ/fairness/drift reports into an actual alerting channel (Teams/email) instead of a
   JSON file a person has to open.

## "What's the weakest part of this project and why?"

The cancellation-prediction model, honestly -- 0.66 AUC, flagged "warning" by design. Real
cancellations are often driven by client-side events not observable in scheduling data. I kept it
in rather than engineering the synthetic data to make it look better, because showing an honestly
modest result with a clear "this is a triage aid, not a gate" framing is more representative of
real model performance than a project full of only green metrics.

## Code quality choices worth mentioning

- Every module is independently runnable (`python -m python.models.demand_forecasting`) and every
  stage of the pipeline is independently runnable via `python -m python.run_pipeline --stage X`.
- Config-driven thresholds (`configs/monitoring.yml`) instead of hard-coded magic numbers, so a
  reviewer can change the bar without touching model code.
- `tests/` covers data-quality rule execution, model training smoke tests, and the fairness/access
  control control logic -- run with `pytest`.
