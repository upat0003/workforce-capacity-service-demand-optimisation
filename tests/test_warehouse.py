"""Verifies the bronze -> silver -> gold build produces a coherent star schema:
no duplicate business keys in dimensions, and every fact FK resolves."""
from __future__ import annotations
from python.utils.duckdb_conn import get_connection


def test_gold_dim_employee_has_unique_keys():
    con = get_connection(read_only=True)
    dupes = con.execute("""
        SELECT count(*) FROM (
            SELECT employee_id, count(*) c FROM gold.dim_employee GROUP BY 1 HAVING count(*) > 1
        )
    """).fetchone()[0]
    con.close()
    assert dupes == 0


def test_gold_fact_service_requests_has_no_orphan_clients():
    con = get_connection(read_only=True)
    orphans = con.execute("""
        SELECT count(*) FROM gold.fact_service_requests r
        LEFT JOIN gold.dim_client c USING (client_id)
        WHERE c.client_id IS NULL
    """).fetchone()[0]
    con.close()
    # gold.fact_service_requests is built only from validated, non-orphan requests
    assert orphans == 0


def test_gold_marts_are_nonempty():
    con = get_connection(read_only=True)
    for table in ("mart_daily_demand", "mart_weekly_overtime", "mart_capacity_utilisation",
                  "mart_service_outcomes", "mart_data_quality"):
        n = con.execute(f"SELECT count(*) FROM gold.{table}").fetchone()[0]
        assert n > 0, f"gold.{table} should not be empty"
    con.close()


def test_fairness_mart_suppresses_small_cohorts():
    con = get_connection(read_only=True)
    min_count = con.execute("SELECT min(shift_count) FROM gold.mart_fairness_workload").fetchone()[0]
    con.close()
    assert min_count >= 8
