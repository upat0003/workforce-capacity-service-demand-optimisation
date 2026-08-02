"""Configuration loading helpers."""
from __future__ import annotations
import os
import yaml
from .paths import CONFIGS


def load_yaml(name: str) -> dict:
    """Load a YAML config file from configs/ by filename, e.g. 'monitoring.yml'."""
    path = CONFIGS / name
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def is_dev_mode() -> bool:
    return os.environ.get("WFCSO_DEV_MODE", "true").lower() not in ("false", "0", "no")


def random_seed() -> int:
    return int(os.environ.get("RANDOM_SEED", "42"))
