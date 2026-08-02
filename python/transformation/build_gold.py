"""Gold layer builder: dimensional star schema and reporting marts. Run standalone with:
    python -m python.transformation.build_gold
"""
from __future__ import annotations
from ..utils.duckdb_conn import get_connection
from ..utils.logging_config import get_logger
from ..utils.paths import SQL

log = get_logger(__name__)

SCRIPTS = [
    "01_dim_date.sql",
    "02_star_schema.sql",
    "03_executive_marts.sql",
    "04_data_quality_marts.sql",
]


def run() -> None:
    con = get_connection()
    for script in SCRIPTS:
        sql_text = (SQL / "gold" / script).read_text()
        con.execute(sql_text)
        log.info("executed gold/%s", script)
    tables = con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='gold' ORDER BY 1").fetchall()
    for (t,) in tables:
        n = con.execute(f"SELECT count(*) FROM gold.{t}").fetchone()[0]
        log.info("gold.%-28s %8d rows", t, n)
    con.close()


if __name__ == "__main__":
    run()
    print("Gold layer built.")
