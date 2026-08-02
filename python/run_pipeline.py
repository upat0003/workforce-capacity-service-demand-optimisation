"""End-to-end pipeline orchestrator: generates synthetic data, builds the
bronze/silver/gold medallion layers, engineers features, trains every model
and decision-support component, runs monitoring and governance checks, and
exports the Power BI sample datasets.

Usage:
    python -m python.run_pipeline --stage all
    python -m python.run_pipeline --stage data       # synthetic data only
    python -m python.run_pipeline --stage warehouse   # bronze -> silver -> gold
    python -m python.run_pipeline --stage features
    python -m python.run_pipeline --stage models
    python -m python.run_pipeline --stage governance
    python -m python.run_pipeline --stage export
"""
from __future__ import annotations
import argparse
import json
import time
from datetime import datetime, timezone

from .utils.logging_config import get_logger
from .utils.paths import ARTIFACTS, ensure_dirs
from .ingestion import generate_synthetic_data
from .transformation import build_bronze, build_silver, build_gold
from .features import feature_engineering
from .models import train_all
from .monitoring import data_quality_monitoring, model_monitoring
from .governance import fairness_checks, access_control, audit_log
from .utils import export_powerbi

log = get_logger(__name__)

STAGES = ["data", "warehouse", "features", "models", "governance", "export"]


def run_stage(stage: str) -> dict:
    t0 = time.time()
    if stage == "data":
        result = generate_synthetic_data.run()
    elif stage == "warehouse":
        build_bronze.run()
        build_silver.run()
        build_gold.run()
        result = {"status": "warehouse built"}
    elif stage == "features":
        result = feature_engineering.run()
    elif stage == "models":
        result = train_all.run()
    elif stage == "governance":
        result = {
            "data_quality": data_quality_monitoring.run(),
            "model_monitoring": model_monitoring.run(),
            "fairness": fairness_checks.run(),
            "access_control": access_control.run(),
            "override_audit": audit_log.run(),
        }
    elif stage == "export":
        result = export_powerbi.run()
    else:
        raise ValueError(f"Unknown stage: {stage}")
    log.info("Stage '%s' completed in %.1fs", stage, time.time() - t0)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["all", *STAGES], default="all")
    args = parser.parse_args()

    ensure_dirs()
    stages = STAGES if args.stage == "all" else [args.stage]
    summary = {"run_started_at": datetime.now(timezone.utc).isoformat(), "stages": {}}
    for stage in stages:
        log.info("=== Running stage: %s ===", stage)
        summary["stages"][stage] = run_stage(stage)

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(f"Pipeline complete. Ran stages: {', '.join(stages)}")
    print(f"See {ARTIFACTS / 'run_summary.json'} for the full run summary.")


if __name__ == "__main__":
    main()
