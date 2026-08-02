"""Shared pytest fixtures. Running the full test suite regenerates the synthetic
data and rebuilds the medallion warehouse once per session so tests are fast
and independent of whatever state the repo was last left in."""
from __future__ import annotations
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

from python.ingestion import generate_synthetic_data  # noqa: E402
from python.transformation import build_bronze, build_silver, build_gold  # noqa: E402
from python.features import feature_engineering  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def built_warehouse():
    """Build bronze/silver/gold and feature tables once for the whole test session."""
    generate_synthetic_data.run()
    build_bronze.run()
    build_silver.run()
    build_gold.run()
    feature_engineering.run()
    yield
