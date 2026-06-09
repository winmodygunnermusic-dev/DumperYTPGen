"""Keymate timeline marker presets."""
from __future__ import annotations

from pathlib import Path

from core.models import KeymateMarker
from core.utils import load_json, save_json


class KeymateManager:
    """Stores timestamp-triggered YTP actions as reusable presets."""

    def __init__(self) -> None:
        self.markers: list[KeymateMarker] = []

    def add_marker(self, marker: KeymateMarker) -> None:
        self.markers.append(marker)
        self.markers.sort(key=lambda item: item.timestamp)

    def markers_between(self, start: float, end: float) -> list[KeymateMarker]:
        return [marker for marker in self.markers if start <= marker.timestamp <= end]

    def save_preset(self, path: Path) -> None:
        save_json(
            path,
            [
                {
                    "timestamp": marker.timestamp,
                    "action": marker.action,
                    "payload": marker.payload,
                    "label": marker.label,
                }
                for marker in self.markers
            ],
        )

    def load_preset(self, path: Path) -> None:
        self.markers = [KeymateMarker(**item) for item in load_json(path, [])]
