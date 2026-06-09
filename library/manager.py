"""Media library persistence and scanning."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from core.models import MediaItem, MediaKind
from core.utils import load_json, save_json
from video.ffprobe_scanner import FFprobeScanner

LOGGER = logging.getLogger(__name__)


class LibraryManager:
    """Tracks source folders and metadata for every media bucket."""

    VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
    AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac"}

    def __init__(self, metadata_path: Path, scanner: Optional[FFprobeScanner] = None) -> None:
        self.metadata_path = metadata_path
        self.scanner = scanner or FFprobeScanner()
        self.folders: dict[MediaKind, Path] = {}
        self.items: dict[MediaKind, list[MediaItem]] = {kind: [] for kind in MediaKind}

    def set_folder(self, kind: MediaKind, folder: Path) -> None:
        self.folders[kind] = folder.expanduser().resolve()
        LOGGER.info("Set %s folder to %s", kind.value, self.folders[kind])

    def load(self) -> None:
        data = load_json(self.metadata_path, {"folders": {}, "items": {}})
        self.folders = {MediaKind(key): Path(value) for key, value in data.get("folders", {}).items()}
        self.items = {kind: [] for kind in MediaKind}
        for key, values in data.get("items", {}).items():
            self.items[MediaKind(key)] = [MediaItem.from_json(item) for item in values]

    def save(self) -> None:
        save_json(
            self.metadata_path,
            {
                "folders": {kind.value: str(path) for kind, path in self.folders.items()},
                "items": {
                    kind.value: [item.to_json() for item in items]
                    for kind, items in self.items.items()
                },
            },
        )

    def scan(self) -> None:
        """Scan configured folders and refresh JSON metadata."""

        for kind, folder in self.folders.items():
            self.items[kind] = self._scan_folder(kind, folder)
        self.save()

    def get_items(self, kind: MediaKind) -> list[MediaItem]:
        return list(self.items.get(kind, []))

    def all_video_sources(self) -> list[MediaItem]:
        return self.get_items(MediaKind.SOURCE_VIDEOS) + self.get_items(MediaKind.MEME_CLIPS)

    def _scan_folder(self, kind: MediaKind, folder: Path) -> list[MediaItem]:
        if not folder.exists():
            LOGGER.warning("Library folder does not exist: %s", folder)
            return []

        items: list[MediaItem] = []
        for path in folder.rglob("*"):
            if not path.is_file() or not self._is_supported(kind, path):
                continue
            item = MediaItem(path=path, kind=kind)
            if path.suffix.lower() in self.VIDEO_EXTENSIONS.union(self.AUDIO_EXTENSIONS):
                try:
                    info = self.scanner.scan(path)
                    item.duration = info.duration
                    item.width = info.width
                    item.height = info.height
                except RuntimeError as exc:
                    LOGGER.warning("Skipping unreadable media %s: %s", path, exc)
                    continue
            items.append(item)
        LOGGER.info("Scanned %d %s items", len(items), kind.value)
        return items

    def _is_supported(self, kind: MediaKind, path: Path) -> bool:
        suffix = path.suffix.lower()
        if kind in {MediaKind.SOURCE_VIDEOS, MediaKind.MEME_CLIPS, MediaKind.TRANSITIONS}:
            return suffix in self.VIDEO_EXTENSIONS
        if kind in {MediaKind.SOURCE_IMAGES, MediaKind.OVERLAYS, MediaKind.CHARACTERS}:
            return suffix in self.IMAGE_EXTENSIONS.union(self.VIDEO_EXTENSIONS)
        if kind in {MediaKind.SOUND_EFFECTS, MediaKind.MUSIC}:
            return suffix in self.AUDIO_EXTENSIONS.union(self.VIDEO_EXTENSIONS)
        return False
