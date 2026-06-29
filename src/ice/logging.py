from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger


def configure_logging(output_root: str | Path | None = None, verbose: bool = True) -> None:
    logger.remove()
    level = "DEBUG" if verbose else "INFO"
    logger.add(sys.stderr, level=level, enqueue=True, backtrace=False, diagnose=False)
    if output_root:
        log_dir = Path(output_root) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        logger.add(log_dir / "ice.log", level="DEBUG", rotation="20 MB", retention=5, enqueue=True)
