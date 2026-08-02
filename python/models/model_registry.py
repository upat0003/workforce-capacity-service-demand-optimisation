"""Lightweight model registry: records every trained model's metrics, threshold
status and artifact path to artifacts/models/registry.json. Stands in for the
Fabric / MLflow model registry a production deployment would use."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from ..utils.paths import ARTIFACTS_MODELS

REGISTRY_PATH = ARTIFACTS_MODELS / "registry.json"


def register(name: str, version: str, metrics: dict, threshold_status: str,
             artifact_path: str, notes: str = "") -> None:
    ARTIFACTS_MODELS.mkdir(parents=True, exist_ok=True)
    registry = []
    if REGISTRY_PATH.exists():
        registry = json.loads(REGISTRY_PATH.read_text())
    registry = [r for r in registry if r["name"] != name]  # replace prior entry for this model
    registry.append({
        "name": name,
        "version": version,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "threshold_status": threshold_status,
        "artifact_path": artifact_path,
        "notes": notes,
    })
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2, default=str))
