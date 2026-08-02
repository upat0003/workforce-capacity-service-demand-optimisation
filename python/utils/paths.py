"""Central path resolution so every module agrees on repo layout."""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CONFIGS = ROOT / "configs"
DATA = ROOT / "data"
DATA_RAW = DATA / "raw"
DATA_REFERENCE = DATA / "reference"
DATA_PROCESSED = DATA / "processed"
DATA_SAMPLES = DATA / "samples"
SQL = ROOT / "sql"
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS_MODELS = ARTIFACTS / "models"
ARTIFACTS_MONITORING = ARTIFACTS / "monitoring"
GOVERNANCE = ROOT / "governance"
POWERBI = ROOT / "powerbi"
POWERBI_DATA = POWERBI / "data"
LOGS = ROOT / "logs"
WAREHOUSE_DB = ARTIFACTS / "warehouse.duckdb"


def ensure_dirs() -> None:
    for p in (DATA_RAW, DATA_REFERENCE, DATA_PROCESSED, DATA_SAMPLES,
              ARTIFACTS_MODELS, ARTIFACTS_MONITORING, POWERBI_DATA, LOGS):
        p.mkdir(parents=True, exist_ok=True)
