"""Audio library and random sound injection helpers."""
from __future__ import annotations

import random

from core.models import AudioInjection, MediaItem


class AudioManager:
    """Builds soundboard entries and YTP-style random audio injections."""

    CATEGORIES = ["meme", "ytp", "cartoon", "voice", "music"]

    def random_injections(
        self,
        sounds: list[MediaItem],
        timeline_duration: float,
        density: float = 0.12,
    ) -> list[AudioInjection]:
        if not sounds or timeline_duration <= 0:
            return []
        count = max(1, int(timeline_duration * density))
        return [
            AudioInjection(
                source=random.choice(sounds).path,
                start=random.uniform(0, max(timeline_duration - 0.2, 0)),
                volume=random.uniform(0.45, 1.0),
            )
            for _ in range(count)
        ]

    def beat_markers(self, bpm: float, duration: float) -> list[float]:
        interval = 60.0 / max(bpm, 1.0)
        markers: list[float] = []
        cursor = 0.0
        while cursor < duration:
            markers.append(round(cursor, 3))
            cursor += interval
        return markers
