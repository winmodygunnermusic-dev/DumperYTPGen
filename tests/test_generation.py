from pathlib import Path

from core.models import MediaItem, MediaKind, OutputFormat
from effects.effect_chain import EffectChain
from video.clip_generator import ClipGenerator


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
