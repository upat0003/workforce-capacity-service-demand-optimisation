"""Trains every model and checks it produces sane, bounded metrics -- a smoke
test that also protects against silent regressions in feature engineering."""
from __future__ import annotations
from python.models import (demand_forecasting, complexity_prediction, cancellation_prediction,
                            service_level_breach_prediction, workload_estimation,
                            capacity_gap_prediction)


def test_demand_forecasting_beats_naive_baseline():
    result = demand_forecasting.run()
    m = result["metrics"]
    assert m["challenger_gbrt_mape"] <= m["baseline_seasonal_naive_mape"]
    assert result["status"] in ("healthy", "warning", "breach")


def test_complexity_prediction_beats_majority_baseline():
    result = complexity_prediction.run()
    m = result["metrics"]
    assert m["challenger_macro_f1"] > m["baseline_majority_class_macro_f1"]


def test_cancellation_prediction_bounded_auc():
    result = cancellation_prediction.run()
    auc = result["metrics"]["challenger_hgb_roc_auc"]
    assert 0.0 <= auc <= 1.0


def test_sla_breach_prediction_beats_urgency_only_baseline():
    result = service_level_breach_prediction.run()
    m = result["metrics"]
    assert m["challenger_hgb_roc_auc"] > m["baseline_urgency_only_roc_auc"]


def test_workload_estimation_produces_finite_mape():
    result = workload_estimation.run()
    assert result["metrics"]["challenger_hgb_mape"] >= 0


def test_capacity_gap_prediction_produces_finite_mae():
    result = capacity_gap_prediction.run()
    assert result["metrics"]["challenger_hgb_mae_fte"] >= 0
