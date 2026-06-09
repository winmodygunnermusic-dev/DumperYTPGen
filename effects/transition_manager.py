"""Transition presets for old-school YTP edits."""
from __future__ import annotations

import random


class TransitionManager:
    """Provides available transition names and filter fragments."""

    TRANSITIONS = [
        "hard_cut",
        "flash_cut",
        "zoom_cut",
        "spin_transition",
        "vhs_glitch",
        "rgb_split",
        "static_noise",
        "tv_shutdown",
        "pixelate",
        "smash_cut",
    ]

    def random_transition(self) -> str:
        return random.choice(self.TRANSITIONS)

    def filter_for(self, name: str) -> str:
        if name == "flash_cut":
            return "fade=t=in:st=0:d=0.05:color=white"
        if name == "vhs_glitch":
            return "noise=alls=18:allf=t+u"
        if name == "pixelate":
            return "scale=iw/8:ih/8,scale=iw*8:ih*8:flags=neighbor"
        if name == "rgb_split":
            return "rgbashift=rh=4:gv=-4:bh=2"
        return "null"
