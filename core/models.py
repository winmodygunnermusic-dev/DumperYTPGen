"""Shared dataclasses and enums for DumperYTPGen."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4


class MediaKind(str, Enum):
    """Supported media library buckets."""

    SOURCE_VIDEOS = "source_videos"
    SOURCE_IMAGES = "source_images"
    SOUND_EFFECTS = "sound_effects"
    MUSIC = "music"
    MEME_CLIPS = "meme_clips"
    OVERLAYS = "overlays"
    TRANSITIONS = "transitions"
    CHARACTERS = "characters"


class OutputFormat(str, Enum):
    """Render output presets."""

    MP4_H264 = "mp4_h264"
    MP4_H265 = "mp4_h265"
    WEBM = "webm"


@dataclass
class MediaItem:
    """A file known to the media library."""

    path: Path
    kind: MediaKind
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    tags: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "kind": self.kind.value,
            "duration": self.duration,
            "width": self.width,
            "height": self.height,
            "tags": self.tags,
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "MediaItem":
        return cls(
            path=Path(data["path"]),
            kind=MediaKind(data["kind"]),
            duration=data.get("duration"),
            width=data.get("width"),
            height=data.get("height"),
            tags=list(data.get("tags", [])),
        )


@dataclass
class ClipSpec:
    """A trimmed source clip and the effects that should be applied to it."""

    source: Path
    start: float
    duration: float
    effects: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: uuid4().hex)


@dataclass
class OverlaySpec:
    """An overlay placed on top of a clip or timeline segment."""

    source: Path
    start: float
    duration: float
    x: int
    y: int
    scale: float = 1.0
    rotation_degrees: float = 0.0


@dataclass
class AudioInjection:
    """A sound effect or voice clip injected into the output timeline."""

    source: Path
    start: float
    volume: float = 1.0


@dataclass
class KeymateMarker:
    """Timeline marker that can trigger effects, overlays, sounds, or transitions."""

    timestamp: float
    action: str
    payload: dict[str, Any] = field(default_factory=dict)
    label: str = ""


@dataclass
class RenderJob:
    """A complete FFmpeg render job."""

    clips: list[ClipSpec]
    output_path: Path
    output_format: OutputFormat = OutputFormat.MP4_H264
    overlays: list[OverlaySpec] = field(default_factory=list)
    audio_injections: list[AudioInjection] = field(default_factory=list)
    transition: str = "hard_cut"
    width: int = 1280
    height: int = 720
    fps: int = 30
    use_hardware_accel: bool = False

    @property
    def estimated_duration(self) -> float:
        return sum(clip.duration for clip in self.clips)
