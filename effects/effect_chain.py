"""FFmpeg filter snippets for classic YTP effects."""
from __future__ import annotations

import random


class EffectChain:
    """Builds video/audio filter snippets from named effects."""

    OLD_SCHOOL_EFFECTS = [
        "reverse_video",
        "stutter",
        "speed_up",
        "slow_motion",
        "freeze_frame",
        "mirror",
        "zoom_spam",
        "shake",
        "hue_rotation",
        "saturation_boost",
        "contrast_boost",
        "datamosh_sim",
        "pitch_shift",
        "audio_chop",
    ]

    @classmethod
    def random_effects(cls, minimum: int = 1, maximum: int = 4) -> list[str]:
        count = random.randint(minimum, maximum)
        return random.sample(cls.OLD_SCHOOL_EFFECTS, k=min(count, len(cls.OLD_SCHOOL_EFFECTS)))

    @staticmethod
    def video_filters(effects: list[str], width: int, height: int, fps: int) -> list[str]:
        filters = [f"scale={width}:{height}:force_original_aspect_ratio=decrease"]
        filters.append(f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2")
        filters.append(f"fps={fps}")
        for effect in effects:
            if effect == "reverse_video":
                filters.append("reverse")
            elif effect == "speed_up":
                filters.append("setpts=0.5*PTS")
            elif effect == "slow_motion":
                filters.append("setpts=1.7*PTS")
            elif effect == "freeze_frame":
                filters.append("tpad=stop_mode=clone:stop_duration=0.15")
            elif effect == "mirror":
                filters.append("hflip")
            elif effect == "zoom_spam":
                filters.append("scale=iw*1.08:ih*1.08,crop=iw/1.08:ih/1.08")
            elif effect == "shake":
                filters.append("crop=iw-24:ih-24:12+8*sin(n):12+8*cos(n)")
            elif effect == "hue_rotation":
                filters.append("hue=h=90*sin(t*8)")
            elif effect == "saturation_boost":
                filters.append("eq=saturation=2.2")
            elif effect == "contrast_boost":
                filters.append("eq=contrast=1.7")
            elif effect == "datamosh_sim":
                filters.append("tblend=all_mode=difference,framestep=2")
            elif effect in {"stutter", "repeat_frames"}:
                filters.append("loop=loop=1:size=3:start=0")
        return filters

    @staticmethod
    def audio_filters(effects: list[str]) -> list[str]:
        filters = ["aresample=48000"]
        for effect in effects:
            if effect == "reverse_audio":
                filters.append("areverse")
            elif effect == "speed_up":
                filters.append("atempo=2.0")
            elif effect == "slow_motion":
                filters.append("atempo=0.7")
            elif effect == "pitch_shift":
                filters.append("asetrate=48000*1.25,aresample=48000")
            elif effect in {"audio_chop", "repeat_words", "sentence_remix"}:
                filters.append("apulsator=hz=8")
        # Ear rape limiter: keep loud meme injections under control.
        filters.append("alimiter=limit=0.85")
        return filters
