"""Sanity checks on the synthetic data generator: correct row counts, expected
columns, and the deliberate data-quality issues actually being present (so we
know the downstream data-quality controls have real work to verify)."""
from __future__ import annotations
import pandas as pd

from python.utils.paths import DATA_RAW, DATA_REFERENCE


def test_reference_tables_exist():
    for name in ("locations", "skills", "service_types", "case_complexity", "service_level_targets"):
        df = pd.read_csv(DATA_REFERENCE / f"{name}.csv")
        assert len(df) > 0


def test_raw_tables_exist_and_nonempty():
    expected = ["employees", "employee_skills", "availability", "leave", "clients",
                "service_requests", "shifts", "overtime", "appointments", "waiting_times",
                "cancellations", "outcomes"]
    for name in expected:
        df = pd.read_csv(DATA_RAW / f"{name}.csv")
        assert len(df) > 0, f"{name} should not be empty"


def test_employees_have_deliberate_duplicates():
    df = pd.read_csv(DATA_RAW / "employees.csv")
    assert df["employee_id"].duplicated().sum() > 0


def test_service_requests_have_missing_complexity_scores():
    df = pd.read_csv(DATA_RAW / "service_requests.csv")
    assert df["complexity_score"].isna().sum() > 0


def test_service_requests_have_orphan_client_references():
    clients = set(pd.read_csv(DATA_RAW / "clients.csv")["client_id"])
    requests = pd.read_csv(DATA_RAW / "service_requests.csv")
    orphans = ~requests["client_id"].isin(clients)
    assert orphans.sum() > 0


def test_employee_skills_have_expired_certifications():
    df = pd.read_csv(DATA_RAW / "employee_skills.csv")
    assert df["expired_flag"].sum() > 0
