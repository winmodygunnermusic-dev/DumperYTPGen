"""Media library persistence and scanning."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, Optional

from core.models import MediaItem, MediaKind
from core.utils import load_json, save_json
from video.ffprobe_scanner import FFprobeScanner

LOGGER = logging.getLogger(__name__)


class LibraryManager:
    """Tracks source folders, direct files, and metadata for every media bucket."""

    VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
    AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac"}

    def __init__(self, metadata_path: Path, scanner: Optional[FFprobeScanner] = None) -> None:
        self.metadata_path = metadata_path
        self.scanner = scanner or FFprobeScanner()
        self.folders: dict[MediaKind, Path] = {}
        self.files: dict[MediaKind, list[Path]] = {kind: [] for kind in MediaKind}
        self.items: dict[MediaKind, list[MediaItem]] = {kind: [] for kind in MediaKind}

    def set_folder(self, kind: MediaKind, folder: Path) -> None:
        self.folders[kind] = folder.expanduser().resolve()
        LOGGER.info("Set %s folder to %s", kind.value, self.folders[kind])

    def set_files(self, kind: MediaKind, files: list[Path]) -> None:
        """Replace the direct multi-file selection for a media bucket."""

        self.files[kind] = self._dedupe_paths(files)
        LOGGER.info("Set %d direct %s files", len(self.files[kind]), kind.value)

    def add_files(self, kind: MediaKind, files: list[Path]) -> None:
        """Append files to a media bucket's direct multi-file selection."""

        self.files[kind] = self._dedupe_paths(self.files.get(kind, []) + files)
        LOGGER.info("Added direct files to %s; now tracking %d", kind.value, len(self.files[kind]))

    def clear_files(self, kind: MediaKind) -> None:
        """Clear direct files for a media bucket while leaving its folder unchanged."""

        self.files[kind] = []

    def load(self) -> None:
        data = load_json(self.metadata_path, {"folders": {}, "files": {}, "items": {}})
        self.folders = {MediaKind(key): Path(value) for key, value in data.get("folders", {}).items()}
        self.files = {kind: [] for kind in MediaKind}
        for key, values in data.get("files", {}).items():
            self.files[MediaKind(key)] = self._dedupe_paths(Path(value) for value in values)
        self.items = {kind: [] for kind in MediaKind}
        for key, values in data.get("items", {}).items():
            self.items[MediaKind(key)] = [MediaItem.from_json(item) for item in values]

    def save(self) -> None:
        save_json(
            self.metadata_path,
            {
                "folders": {kind.value: str(path) for kind, path in self.folders.items()},
                "files": {
                    kind.value: [str(path) for path in paths]
                    for kind, paths in self.files.items()
                    if paths
                },
                "items": {
                    kind.value: [item.to_json() for item in items]
                    for kind, items in self.items.items()
                },
            },
        )

    def scan(self) -> None:
        """Scan configured folders and direct files, then refresh JSON metadata."""

        for kind in MediaKind:
            found: list[MediaItem] = []
            folder = self.folders.get(kind)
            if folder is not None:
                found.extend(self._scan_folder(kind, folder))
            found.extend(self._scan_direct_files(kind, self.files.get(kind, [])))
            self.items[kind] = self._dedupe_items(found)
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
            item = self._scan_file(kind, path)
            if item is not None:
                items.append(item)
        LOGGER.info("Scanned %d %s items from folder %s", len(items), kind.value, folder)
        return items

    def _scan_direct_files(self, kind: MediaKind, files: list[Path]) -> list[MediaItem]:
        items: list[MediaItem] = []
        for path in files:
            item = self._scan_file(kind, path)
            if item is not None:
                items.append(item)
        LOGGER.info("Scanned %d direct %s files", len(items), kind.value)
        return items

    def _scan_file(self, kind: MediaKind, path: Path) -> Optional[MediaItem]:
        if not path.is_file() or not self._is_supported(kind, path):
            return None
        item = MediaItem(path=path, kind=kind)
        if path.suffix.lower() in self.VIDEO_EXTENSIONS.union(self.AUDIO_EXTENSIONS):
            try:
                info = self.scanner.scan(path)
                item.duration = info.duration
                item.width = info.width
                item.height = info.height
            except RuntimeError as exc:
                LOGGER.warning("Skipping unreadable media %s: %s", path, exc)
                return None
        return item

    def _is_supported(self, kind: MediaKind, path: Path) -> bool:
        suffix = path.suffix.lower()
        if kind in {MediaKind.SOURCE_VIDEOS, MediaKind.MEME_CLIPS, MediaKind.TRANSITIONS}:
            return suffix in self.VIDEO_EXTENSIONS
        if kind in {MediaKind.SOURCE_IMAGES, MediaKind.OVERLAYS, MediaKind.CHARACTERS}:
            return suffix in self.IMAGE_EXTENSIONS.union(self.VIDEO_EXTENSIONS)
        if kind in {MediaKind.SOUND_EFFECTS, MediaKind.MUSIC}:
            return suffix in self.AUDIO_EXTENSIONS.union(self.VIDEO_EXTENSIONS)
        return False

    def _dedupe_paths(self, paths: Iterable[Path]) -> list[Path]:
        deduped: dict[str, Path] = {}
        for path in paths:
            resolved = Path(path).expanduser().resolve()
            deduped[str(resolved)] = resolved
        return list(deduped.values())

    def _dedupe_items(self, items: list[MediaItem]) -> list[MediaItem]:
        deduped: dict[str, MediaItem] = {}
        for item in items:
            deduped[str(item.path.resolve())] = item
        return list(deduped.values())
