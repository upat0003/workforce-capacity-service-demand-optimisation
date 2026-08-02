"""Simulated role-based access control check, driven by configs/access_control.yml.
This exercises the same policy documented in governance/access_control_matrix.md
against a sample of representative access requests, producing an evidence log
for the Data Quality and Governance dashboard page. It is a design/test harness,
not a network-level enforcement point -- in production this policy would be
implemented as Fabric workspace roles, row-level security and Purview
sensitivity labels.
"""
from __future__ import annotations
import json
from dataclasses import dataclass

from ..utils.config import load_yaml
from ..utils.logging_config import get_logger
from ..utils.paths import ARTIFACTS_MONITORING

log = get_logger(__name__)


@dataclass
class AccessRequest:
    role: str
    dataset: str
    wants_pii: bool
    region: str | None = None


SAMPLE_REQUESTS = [
    AccessRequest("workforce_analyst", "gold", wants_pii=False),
    AccessRequest("workforce_analyst", "bronze.employees", wants_pii=True),          # expected: denied
    AccessRequest("regional_coordinator", "silver", wants_pii=True, region="LOC-02"),
    AccessRequest("executive", "gold.executive_marts", wants_pii=False),
    AccessRequest("executive", "silver", wants_pii=True),                            # expected: denied
    AccessRequest("people_and_culture", "bronze.employees", wants_pii=True),
    AccessRequest("data_platform_engineer", "artifacts", wants_pii=False),
    AccessRequest("model_risk_reviewer", "governance", wants_pii=False),
    AccessRequest("model_risk_reviewer", "bronze.employees", wants_pii=True),         # expected: denied
]


def check_access(policy: dict, req: AccessRequest) -> dict:
    role_policy = policy["roles"].get(req.role)
    if role_policy is None:
        return {"decision": "denied", "reason": "unknown role"}
    dataset_allowed = any(req.dataset == d or req.dataset.startswith(d.split(".")[0]) for d in role_policy["datasets"])
    if not dataset_allowed:
        return {"decision": "denied", "reason": f"role '{req.role}' has no grant for dataset '{req.dataset}'"}
    if req.wants_pii and not role_policy.get("can_view_pii", False):
        return {"decision": "denied", "reason": "PII access requires can_view_pii grant"}
    row_filter = role_policy.get("row_level_filter")
    return {"decision": "allowed", "row_level_filter": row_filter, "region_scope": req.region}


def run() -> dict:
    policy = load_yaml("access_control.yml")
    results = []
    for req in SAMPLE_REQUESTS:
        outcome = check_access(policy, req)
        results.append({"role": req.role, "dataset": req.dataset, "wants_pii": req.wants_pii, **outcome})

    summary = {
        "requests_evaluated": len(results),
        "allowed": sum(1 for r in results if r["decision"] == "allowed"),
        "denied": sum(1 for r in results if r["decision"] == "denied"),
        "results": results,
    }
    ARTIFACTS_MONITORING.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS_MONITORING / "access_control_check.json").write_text(json.dumps(summary, indent=2))
    log.info("Access control check: allowed=%d denied=%d", summary["allowed"], summary["denied"])
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
