"""Random clip generation from scanned source videos."""
from __future__ import annotations

import logging
import random
from pathlib import Path

from core.models import ClipSpec, MediaItem
from effects.effect_chain import EffectChain

LOGGER = logging.getLogger(__name__)


class ClipGenerator:
    """Creates random trimmed clip specs for the render engine."""

    CLIP_LENGTHS = [0.2, 0.5, 1.0, 2.0, 3.0, 5.0]

    def generate(self, sources: list[MediaItem], target_duration: float, old_school: bool = True) -> list[ClipSpec]:
        videos = [item for item in sources if item.duration and item.duration > 0.25]
        if not videos:
            raise ValueError("No scanned source videos are available.")

        clips: list[ClipSpec] = []
        elapsed = 0.0
        while elapsed < target_duration:
            source = random.choice(videos)
            clip_length = min(random.choice(self.CLIP_LENGTHS), target_duration - elapsed, source.duration or 0)
            if clip_length <= 0:
                break
            max_start = max((source.duration or clip_length) - clip_length, 0.0)
            start = random.uniform(0.0, max_start) if max_start else 0.0
            effects = EffectChain.random_effects(1, 5 if old_school else 3)
            clips.append(ClipSpec(source=Path(source.path), start=start, duration=clip_length, effects=effects))
            elapsed += clip_length
        LOGGER.info("Generated %d clips for %.2fs timeline", len(clips), target_duration)
        return clips
