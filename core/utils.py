"""Small cross-platform utility helpers."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Optional

from core.platform_compat import bundled_tool_candidates


def ensure_tool(name: str, app_root: Optional[Path] = None) -> str:
    """Return a tool executable path or raise a helpful cross-platform error.

    Resolution order:
    1. Explicit absolute/relative path supplied by the caller.
    2. Optional bundled app paths such as ``assets/bin/ffmpeg.exe``.
    3. The operating system ``PATH``.
    """

    candidate = Path(name)
    if candidate.parent != Path(".") and candidate.exists():
        return str(candidate)

    if app_root is not None:
        for bundled in bundled_tool_candidates(name, app_root):
            if bundled.exists():
                return str(bundled)

    executable = shutil.which(name)
    if executable is None:
        hint = " Install FFmpeg/FFprobe or place the executable in assets/bin."
        raise RuntimeError(f"Required executable '{name}' was not found on PATH.{hint}")
    return executable


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, sort_keys=True)
