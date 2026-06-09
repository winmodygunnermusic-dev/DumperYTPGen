"""Random overlay placement for images, memes, characters, and explosions."""
from __future__ import annotations

import random

from core.models import MediaItem, OverlaySpec


class OverlayManager:
    """Creates random overlay specs with position, scale, and rotation."""

    def random_overlays(
        self,
        overlay_items: list[MediaItem],
        timeline_duration: float,
        width: int = 1280,
        height: int = 720,
        density: float = 0.08,
    ) -> list[OverlaySpec]:
        if not overlay_items or timeline_duration <= 0:
            return []
        count = max(1, int(timeline_duration * density))
        return [
            OverlaySpec(
                source=random.choice(overlay_items).path,
                start=random.uniform(0, max(timeline_duration - 0.2, 0)),
                duration=random.choice([0.2, 0.5, 1.0, 2.0]),
                x=random.randint(0, max(width - 160, 0)),
                y=random.randint(0, max(height - 120, 0)),
                scale=random.uniform(0.25, 1.4),
                rotation_degrees=random.choice([0, 0, 0, -15, 15, 45, -45]),
            )
            for _ in range(count)
        ]
