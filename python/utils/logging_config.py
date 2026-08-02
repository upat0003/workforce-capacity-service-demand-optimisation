"""Standard logging setup, consistent across every entrypoint in the platform."""
from __future__ import annotations
import logging
import logging.config
import yaml
from .paths import CONFIGS, LOGS

_CONFIGURED = False


def setup_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    LOGS.mkdir(parents=True, exist_ok=True)
    cfg_path = CONFIGS / "logging.yml"
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as fh:
            cfg = yaml.safe_load(fh)
        logging.config.dictConfig(cfg)
    else:
        logging.basicConfig(level=logging.INFO)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
