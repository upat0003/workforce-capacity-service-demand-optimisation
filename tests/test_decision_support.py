"""Smoke tests for the deterministic decision-support components (not trained
models): skill matching, the scheduling optimiser, shift recommendations and
scenario planning."""
from __future__ import annotations
from python.models import skill_matching, scheduling_optimiser, shift_recommendation, scenario_planning
from python.models import workload_estimation, capacity_gap_prediction


def test_skill_matching_scores_open_requests():
    # workload/capacity models don't need to run first for this component
    result = skill_matching.run()
    assert result["requests_scored"] >= 0


def test_scheduling_optimiser_fill_rate_bounded():
    result = scheduling_optimiser.run()
    assert 0 <= result["fill_rate_pct"] <= 100
    assert result["requests_assigned"] + result["requests_unassigned"] == result["requests_considered"]
    assert 0 <= result["workload_gini_coefficient"] <= 1


def test_shift_recommendation_runs(tmp_path):
    workload_estimation.run()
    capacity_gap_prediction.run()
    result = shift_recommendation.run()
    assert "week_start_date" in result


def test_scenario_planning_produces_five_scenarios():
    workload_estimation.run()
    result = scenario_planning.run()
    assert len(result["scenarios"]) == 5
    for row in result["scenarios"]:
        assert row["capacity_gap_fte"] is not None
