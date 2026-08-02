"""Silver layer builder: cleaning, conformance, deduplication and referential
integrity flagging on top of bronze. Run standalone with:
    python -m python.transformation.build_silver
"""
from __future__ import annotations
from ..utils.duckdb_conn import get_connection
from ..utils.logging_config import get_logger
from ..utils.paths import SQL

log = get_logger(__name__)

SCRIPTS = [
    "01_dim_reference.sql",
    "02_dim_employee.sql",
    "03_dim_client_fact_requests.sql",
    "04_fact_shifts_overtime.sql",
    "05_fact_appointments_outcomes.sql",
]


def run() -> None:
    con = get_connection()
    for script in SCRIPTS:
        sql_text = (SQL / "silver" / script).read_text()
        con.execute(sql_text)
        log.info("executed silver/%s", script)
    tables = con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='silver' ORDER BY 1").fetchall()
    for (t,) in tables:
        n = con.execute(f"SELECT count(*) FROM silver.{t}").fetchone()[0]
        log.info("silver.%-24s %8d rows", t, n)
    con.close()


if __name__ == "__main__":
    run()
    print("Silver layer built.")
