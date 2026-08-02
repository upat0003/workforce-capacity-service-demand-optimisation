"""Bronze layer builder: loads synthetic source extracts into DuckDB, standing in
for the Fabric Lakehouse ingestion zone. Run standalone with:
    python -m python.transformation.build_bronze
"""
from __future__ import annotations
from ..utils.duckdb_conn import get_connection
from ..utils.logging_config import get_logger
from ..utils.paths import SQL, DATA_RAW, DATA_REFERENCE

log = get_logger(__name__)


def run() -> None:
    con = get_connection()
    sql_text = (SQL / "bronze" / "01_load_raw_extracts.sql").read_text()
    sql_text = sql_text.format(raw_dir=DATA_RAW.as_posix(), reference_dir=DATA_REFERENCE.as_posix())
    con.execute(sql_text)
    tables = con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='bronze' ORDER BY 1").fetchall()
    for (t,) in tables:
        n = con.execute(f"SELECT count(*) FROM bronze.{t}").fetchone()[0]
        log.info("bronze.%-24s %8d rows", t, n)
    con.close()


if __name__ == "__main__":
    run()
    print("Bronze layer built.")
