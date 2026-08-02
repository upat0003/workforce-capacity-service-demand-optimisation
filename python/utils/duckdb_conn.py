"""DuckDB connection helper. Locally this plays the role a Fabric Lakehouse /
Warehouse SQL endpoint would play in a production deployment: one physical
database, three logical schemas (bronze, silver, gold)."""
from __future__ import annotations
import duckdb
from .paths import WAREHOUSE_DB, ARTIFACTS


def get_connection(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(WAREHOUSE_DB), read_only=read_only)
    if not read_only:
        for schema in ("bronze", "silver", "gold"):
            con.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    return con
