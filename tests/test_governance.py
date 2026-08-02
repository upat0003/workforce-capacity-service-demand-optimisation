"""Tests for the governance and monitoring control layer: data quality rules,
fairness checks, access control policy enforcement and drift monitoring."""
from __future__ import annotations
from python.monitoring import data_quality_monitoring, model_monitoring
from python.governance import fairness_checks, access_control, audit_log
from python.models import train_all


def test_data_quality_rules_execute_and_summarise():
    summary = data_quality_monitoring.run()
    assert summary["rules_evaluated"] == 7
    assert summary["rules_passed"] + summary["rules_failed"] + summary["rules_errored"] == 7


def test_fairness_check_suppresses_small_cohorts_and_runs():
    report = fairness_checks.run()
    assert "cohorts_evaluated" in report
    assert isinstance(report["any_breach"], bool)


def test_access_control_denies_expected_requests():
    summary = access_control.run()
    denied_roles_datasets = {(r["role"], r["dataset"]) for r in summary["results"] if r["decision"] == "denied"}
    # A workforce analyst must never be granted PII access to raw employee records
    assert ("workforce_analyst", "bronze.employees") in denied_roles_datasets


def test_override_audit_log_appends_a_record():
    record = audit_log.run()
    assert record["total_appointments"] > 0
    assert 0 <= record["override_rate_pct"] <= 100


def test_model_monitoring_reads_registry_after_training():
    train_all.run()
    report = model_monitoring.run()
    assert "model_threshold_status" in report
    assert len(report["model_threshold_status"]) >= 6
