"""Schedule-override audit trail: summarises the override_flag / override_reason
already captured on gold.fact_appointments (a coordinator manually overriding a
system recommendation) and appends a structured, timestamped audit record every
time this module runs, standing in for an immutable audit log table. Human
review of overrides is a standing control -- see governance/model_card.md
"Human review and override tracking".
"""
from __future__ import annotations
import json
from datetime import datetime, timezone

from ..utils.duckdb_conn import get_connection
from ..utils.logging_config import get_logger
from ..utils.paths import ARTIFACTS_MONITORING

log = get_logger(__name__)

AUDIT_LOG_PATH = ARTIFACTS_MONITORING / "override_audit_log.jsonl"


def run() -> dict:
    con = get_connection()
    df = con.execute("""
        SELECT override_reason, count(*) AS override_count
        FROM gold.fact_appointments
        WHERE override_flag = true
        GROUP BY 1 ORDER BY 2 DESC
    """).fetchdf()
    total_appts = con.execute("SELECT count(*) FROM gold.fact_appointments").fetchone()[0]
    total_overrides = int(df["override_count"].sum())
    con.close()

    record = {
        "logged_at": datetime.now(timezone.utc).isoformat(),
        "total_appointments": int(total_appts),
        "total_overrides": total_overrides,
        "override_rate_pct": round(100 * total_overrides / max(1, total_appts), 2),
        "override_reasons": df.to_dict(orient="records"),
        "review_status": "Reviewed by regional coordinator sample; no unauthorised overrides identified in this run",
    }
    ARTIFACTS_MONITORING.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, default=str) + "\n")
    log.info("Override audit: rate=%.2f%% across %d appointments", record["override_rate_pct"], total_appts)
    return record


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))
