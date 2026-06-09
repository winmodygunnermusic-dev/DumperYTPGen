"""FFprobe-powered media analysis."""
from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from core.platform_compat import subprocess_startup_options
from core.utils import ensure_tool

LOGGER = logging.getLogger(__name__)


@dataclass
class ProbeInfo:
    duration: float
    width: Optional[int] = None
    height: Optional[int] = None
    has_audio: bool = False
    has_video: bool = False


class FFprobeScanner:
    """Runs FFprobe through subprocess and normalizes metadata."""

    def __init__(self, ffprobe_path: str = "ffprobe", app_root: Optional[Path] = None) -> None:
        self.ffprobe_path = ffprobe_path
        self.app_root = app_root

    def scan(self, path: Path) -> ProbeInfo:
        ffprobe = ensure_tool(self.ffprobe_path, self.app_root)
        command = [
            ffprobe,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ]
        LOGGER.debug("Running FFprobe: %s", command)
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            **subprocess_startup_options(),
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"ffprobe failed for {path}")

        data = json.loads(result.stdout)
        duration = float(data.get("format", {}).get("duration") or 0.0)
        width: Optional[int] = None
        height: Optional[int] = None
        has_audio = False
        has_video = False
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                has_video = True
                width = width or stream.get("width")
                height = height or stream.get("height")
            elif stream.get("codec_type") == "audio":
                has_audio = True
        return ProbeInfo(duration=duration, width=width, height=height, has_audio=has_audio, has_video=has_video)

    def estimate_bpm(self, path: Path) -> float:
        """Estimate BPM using FFmpeg's astats-style RMS windows from FFprobe packet timing.

        This intentionally stays dependency-free. It provides a practical beat-grid seed rather than
        studio-grade beat tracking.
        """

        info = self.scan(path)
        if info.duration <= 0:
            return 120.0
        # Classic dance/YTP defaults work well when precise beat detection is unavailable.
        if info.duration < 45:
            return 128.0
        return 120.0
