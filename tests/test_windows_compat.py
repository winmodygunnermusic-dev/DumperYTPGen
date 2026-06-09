from pathlib import Path

from core.platform_compat import bundled_tool_candidates
from core.utils import ensure_tool


def test_bundled_tool_candidates_include_windows_81_folder() -> None:
    candidates = bundled_tool_candidates("ffmpeg", Path("/app"))
    assert Path("/app/assets/bin/win8.1/ffmpeg") in candidates or Path(
        "/app/assets/bin/win8.1/ffmpeg.exe"
    ) in candidates


def test_ensure_tool_prefers_bundled_executable(tmp_path: Path) -> None:
    tool = tmp_path / "assets" / "bin" / "ffprobe"
    tool.parent.mkdir(parents=True)
    tool.write_text("fake", encoding="utf-8")
    assert ensure_tool("ffprobe", tmp_path) == str(tool)
