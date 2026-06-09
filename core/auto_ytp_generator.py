"""One-click automatic YTP timeline assembly."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from audio.manager import AudioManager
from core.models import MediaKind, OutputFormat, RenderJob
from effects.overlay_manager import OverlayManager
from effects.transition_manager import TransitionManager
from library.manager import LibraryManager
from video.clip_generator import ClipGenerator


class AutoYTPGenerator:
    """Coordinates clip, overlay, audio, and transition randomization."""

    DURATION_PRESETS = {
        "1 minute": 60,
        "3 minutes": 180,
        "5 minutes": 300,
        "10 minutes": 600,
    }

    def __init__(
        self,
        library_manager: LibraryManager,
        clip_generator: Optional[ClipGenerator] = None,
        audio_manager: Optional[AudioManager] = None,
        overlay_manager: Optional[OverlayManager] = None,
        transition_manager: Optional[TransitionManager] = None,
    ) -> None:
        self.library_manager = library_manager
        self.clip_generator = clip_generator or ClipGenerator()
        self.audio_manager = audio_manager or AudioManager()
        self.overlay_manager = overlay_manager or OverlayManager()
        self.transition_manager = transition_manager or TransitionManager()

    def build_job(
        self,
        duration_label: str,
        output_path: Path,
        output_format: OutputFormat = OutputFormat.MP4_H264,
        old_school_mode: bool = True,
        width: int = 1280,
        height: int = 720,
        fps: int = 30,
    ) -> RenderJob:
        target_duration = float(self.DURATION_PRESETS[duration_label])
        clips = self.clip_generator.generate(
            self.library_manager.all_video_sources(),
            target_duration=target_duration,
            old_school=old_school_mode,
        )
        timeline_duration = sum(clip.duration for clip in clips)
        overlays = self.overlay_manager.random_overlays(
            self.library_manager.get_items(MediaKind.OVERLAYS)
            + self.library_manager.get_items(MediaKind.CHARACTERS)
            + self.library_manager.get_items(MediaKind.SOURCE_IMAGES),
            timeline_duration=timeline_duration,
            width=width,
            height=height,
        )
        sounds = self.library_manager.get_items(MediaKind.SOUND_EFFECTS)
        audio_injections = self.audio_manager.random_injections(sounds, timeline_duration)
        return RenderJob(
            clips=clips,
            output_path=output_path,
            output_format=output_format,
            overlays=overlays,
            audio_injections=audio_injections,
            transition=self.transition_manager.random_transition(),
            width=width,
            height=height,
            fps=fps,
        )
