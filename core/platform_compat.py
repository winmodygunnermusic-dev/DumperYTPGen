"""Platform compatibility helpers, including Windows 8.1 support.

The application intentionally avoids Windows 10-only APIs.  These helpers centralize
small subprocess and OS-version differences so FFmpeg/FFprobe calls behave the same
on Windows 8.1, newer Windows releases, and Linux.
"""
from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path
from typing import Any


WINDOWS_81_RELEASE = "8.1"


def is_windows() -> bool:
    """Return ``True`` when running on any Windows version."""

    return os.name == "nt"


def is_windows_81() -> bool:
    """Return ``True`` when the host reports Windows 8.1."""

    return is_windows() and platform.release() == WINDOWS_81_RELEASE


def platform_label() -> str:
    """Return a concise, user-facing platform label for diagnostics."""

    if is_windows():
        return f"Windows {platform.release()} ({platform.version()})"
    return f"{platform.system()} {platform.release()}"


def subprocess_startup_options() -> dict[str, Any]:
    """Return subprocess options that are safe on Windows 8.1 and no-ops elsewhere.

    Tkinter apps on Windows should not flash a console window every time FFmpeg or
    FFprobe starts.  ``STARTF_USESHOWWINDOW`` and ``CREATE_NO_WINDOW`` are long-lived
    Win32 flags that work on Windows 8.1, so they are safe for the requested legacy
    target while remaining harmless for newer Windows versions.
    """

    if not is_windows():
        return {}

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return {
        "startupinfo": startupinfo,
        "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0),
    }


def bundled_tool_candidates(tool_name: str, app_root: Path) -> list[Path]:
    """Return bundled executable locations to check before falling back to PATH.

    Users on Windows 8.1 often install FFmpeg manually instead of through package
    managers.  Supporting a local ``assets/bin`` drop-in keeps the app portable:
    ``assets/bin/ffmpeg.exe`` and ``assets/bin/win8.1/ffmpeg.exe`` are both accepted.
    """

    names = [tool_name]
    if is_windows() and not tool_name.lower().endswith(".exe"):
        names.insert(0, f"{tool_name}.exe")

    roots = [app_root / "assets" / "bin", app_root / "assets" / "bin" / "win8.1"]
    return [root / name for root in roots for name in names]
