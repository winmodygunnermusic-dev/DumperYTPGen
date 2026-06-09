"""Application logging setup."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional


def configure_logging(log_dir: Optional[Path] = None) -> None:
    """Configure console and optional file logging once."""

    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_dir / "dumperytpgen.log", encoding="utf-8"))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )
