"""Runs the rule set defined in governance/data_quality_rules.yml against the
silver and gold layers, and writes a pass/fail control report used by the Data
Quality and Governance dashboard page and by CI (tests/test_data_quality.py
imports this module directly).
"""
from __future__ import annotations
import json
import yaml
import pandas as pd

from ..utils.duckdb_conn import get_connection
from ..utils.logging_config import get_logger
from ..utils.paths import ARTIFACTS_MONITORING, ROOT

log = get_logger(__name__)

RULES_PATH = ROOT / "governance" / "data_quality_rules.yml"


def run() -> dict:
    con = get_connection()
    rules = yaml.safe_load(RULES_PATH.read_text())["rules"]

    results = []
    for rule in rules:
        try:
            row = con.execute(rule["check_sql"]).fetchone()
            failing, total = int(row[0] or 0), int(row[1] or 0)
        except Exception as exc:  # pragma: no cover - defensive; surfaces as a failed rule
            log.error("Data quality rule '%s' failed to execute: %s", rule["rule_id"], exc)
            failing, total = -1, 0
        pass_rate = round(100 * (1 - failing / total), 2) if total > 0 and failing >= 0 else None
        status = "error" if failing < 0 else ("fail" if pass_rate is not None and pass_rate < rule["min_pass_rate_pct"] else "pass")
        results.append({
            "rule_id": rule["rule_id"], "dataset": rule["dataset"], "description": rule["description"],
            "severity": rule["severity"], "failing_rows": failing, "total_rows": total,
            "pass_rate_pct": pass_rate, "min_pass_rate_pct": rule["min_pass_rate_pct"], "status": status,
        })
    con.close()

    df = pd.DataFrame(results)
    ARTIFACTS_MONITORING.mkdir(parents=True, exist_ok=True)
    df.to_csv(ARTIFACTS_MONITORING / "data_quality_report.csv", index=False)

    summary = {
        "rules_evaluated": len(df),
        "rules_passed": int((df["status"] == "pass").sum()),
        "rules_failed": int((df["status"] == "fail").sum()),
        "rules_errored": int((df["status"] == "error").sum()),
        "overall_pass_rate_pct": round(float(df["pass_rate_pct"].mean()), 2) if df["pass_rate_pct"].notna().any() else None,
    }
    (ARTIFACTS_MONITORING / "data_quality_summary.json").write_text(json.dumps(summary, indent=2))
    log.info("Data quality monitoring: %s", summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
