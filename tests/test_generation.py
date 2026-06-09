from pathlib import Path

from core.models import MediaItem, MediaKind, OutputFormat
from effects.effect_chain import EffectChain
from library.manager import LibraryManager
from video.clip_generator import ClipGenerator
from video.ffprobe_scanner import ProbeInfo


def test_clip_generator_reaches_target_duration() -> None:
    item = MediaItem(path=Path("source.mp4"), kind=MediaKind.SOURCE_VIDEOS, duration=10.0)
    clips = ClipGenerator().generate([item], target_duration=3.0)
    assert clips
    assert round(sum(clip.duration for clip in clips), 3) == 3.0
    assert all(clip.source == Path("source.mp4") for clip in clips)


def test_effect_chain_contains_required_normalization_filters() -> None:
    filters = EffectChain.video_filters(["mirror", "contrast_boost"], width=1280, height=720, fps=30)
    assert "fps=30" in filters
    assert "hflip" in filters
    assert any(item.startswith("eq=contrast") for item in filters)


def test_output_format_values_are_stable() -> None:
    assert OutputFormat.MP4_H264.value == "mp4_h264"
    assert OutputFormat.MP4_H265.value == "mp4_h265"
    assert OutputFormat.WEBM.value == "webm"


class FakeScanner:
    def scan(self, path: Path) -> ProbeInfo:
        return ProbeInfo(duration=4.0, width=640, height=360, has_audio=True, has_video=True)


def test_library_manager_scans_direct_multi_file_materials(tmp_path: Path) -> None:
    video = tmp_path / "clip.mp4"
    image = tmp_path / "overlay.png"
    duplicate = tmp_path / "duplicate.mp4"
    ignored = tmp_path / "notes.txt"
    for path in (video, image, duplicate, ignored):
        path.write_text("fake", encoding="utf-8")

    manager = LibraryManager(tmp_path / "library.json", scanner=FakeScanner())
    manager.add_files(MediaKind.SOURCE_VIDEOS, [video, duplicate, video, ignored])
    manager.add_files(MediaKind.OVERLAYS, [image])
    manager.scan()

    videos = manager.get_items(MediaKind.SOURCE_VIDEOS)
    overlays = manager.get_items(MediaKind.OVERLAYS)
    assert [item.path for item in videos] == [video.resolve(), duplicate.resolve()]
    assert videos[0].duration == 4.0
    assert [item.path for item in overlays] == [image.resolve()]

    loaded = LibraryManager(tmp_path / "library.json", scanner=FakeScanner())
    loaded.load()
    assert loaded.files[MediaKind.SOURCE_VIDEOS] == [video.resolve(), duplicate.resolve(), ignored.resolve()]
    assert loaded.files[MediaKind.OVERLAYS] == [image.resolve()]
