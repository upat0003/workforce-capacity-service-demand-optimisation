# Access Control Matrix

Enforced in the demo by `python/governance/access_control.py`, driven by `configs/access_control.yml`.
In a production Fabric deployment this maps to workspace roles, Lakehouse/Warehouse SQL
permissions, row-level security predicates and Purview sensitivity labels.

| Role | Datasets | Can view PII | Can override schedule | Can approve leave | Row-level scope |
|---|---|---|---|---|---|
| Workforce Analyst | gold, silver, powerbi extracts | No | No | No | None |
| Regional Coordinator | gold, silver, powerbi extracts | Yes | Yes | Yes | Own assigned region only |
| People & Culture | bronze.employees, silver, gold, powerbi extracts | Yes | No | Yes | None |
| Executive | gold executive marts, powerbi extracts | No | No | No | None (aggregate only) |
| Data Platform Engineer | bronze, silver, gold, artifacts | No | No | No | None |
| Model Risk Reviewer | artifacts.monitoring, governance | No | No | No | None |

## Control test evidence

Every pipeline run exercises a representative sample of access requests against this matrix
(`python/governance/access_control.py::SAMPLE_REQUESTS`) and writes the allow/deny decision and
reason to `artifacts/monitoring/access_control_check.json`. Denied-by-design cases are included
deliberately (e.g. a Workforce Analyst requesting `bronze.employees` with PII, an Executive
requesting row-level `silver`) so the control test fails loudly if the policy engine ever grants
an unintended access.

## Segregation of duties

- No role can both train/deploy a model (`data_platform_engineer`) and independently approve its
  fairness sign-off (`model_risk_reviewer`) -- these are held by different functions.
- Schedule overrides (`regional_coordinator`) are logged and reviewed independently by People &
  Culture and Model Risk on a sampling basis (see `governance/model_card.md` and
  `python/governance/audit_log.py`).
- Executives receive aggregate-only, PII-free marts; there is no path for an executive credential
  to reach row-level client or employee detail.

## Review cadence

This matrix is reviewed quarterly and at any change to `configs/access_control.yml`, in line
with the model and control review cadence in `governance/model_card.md`.
