"""Project save/load/autosave support."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from core.utils import load_json, save_json


class ProjectManager:
    """Persists project settings and render queue data."""

    def __init__(self, autosave_path: Path) -> None:
        self.autosave_path = autosave_path
        self.current_project: dict[str, Any] = {}

    def new_project(self, name: str = "Untitled YTP") -> None:
        self.current_project = {"name": name, "settings": {}, "render_queue": []}

    def save_project(self, path: Optional[Path] = None) -> None:
        save_json(path or self.autosave_path, self.current_project)

    def load_project(self, path: Path) -> dict[str, Any]:
        self.current_project = load_json(path, {})
        return self.current_project

    def export_settings(self, path: Path) -> None:
        save_json(path, self.current_project.get("settings", {}))

    def import_settings(self, path: Path) -> None:
        self.current_project.setdefault("settings", {}).update(load_json(path, {}))

    def autosave(self) -> None:
        self.save_project(self.autosave_path)
