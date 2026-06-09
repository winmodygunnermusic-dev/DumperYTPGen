"""Application entry point for DumperYTPGen."""
from __future__ import annotations

import logging
from pathlib import Path

from core.auto_ytp_generator import AutoYTPGenerator
from core.logging_config import configure_logging
from core.platform_compat import platform_label
from gui.main_window import MainWindow
from library.manager import LibraryManager
from projects.project_manager import ProjectManager
from render.engine import RenderEngine
from video.ffprobe_scanner import FFprobeScanner


def main() -> None:
    app_data = Path.home() / ".dumperytpgen"
    configure_logging(app_data / "logs")
    # Platform diagnostics help users on legacy systems such as Windows 8.1
    # confirm that the app is not relying on Windows 10+ APIs.
    logging.getLogger(__name__).info("Starting DumperYTPGen on %s", platform_label())
    app_root = Path(__file__).resolve().parent.parent
    library_manager = LibraryManager(
        app_data / "library_metadata.json", scanner=FFprobeScanner(app_root=app_root)
    )
    project_manager = ProjectManager(app_data / "autosave_project.json")
    project_manager.new_project("DumperYTPGen Autosave")
    generator = AutoYTPGenerator(library_manager)
    render_engine = RenderEngine(app_root=app_root)
    window = MainWindow(library_manager, generator, render_engine, project_manager)
    window.mainloop()


if __name__ == "__main__":
    main()
