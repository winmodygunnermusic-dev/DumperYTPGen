"""Thread-safe FFmpeg render engine."""
from __future__ import annotations

import logging
import subprocess
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Optional

from core.models import OutputFormat, RenderJob
from core.platform_compat import subprocess_startup_options
from core.utils import ensure_tool
from effects.effect_chain import EffectChain

LOGGER = logging.getLogger(__name__)
ProgressCallback = Callable[[float, str], None]


class RenderEngine:
    """Renders clip timelines with FFmpeg subprocesses on background threads."""

    def __init__(self, ffmpeg_path: str = "ffmpeg", app_root: Optional[Path] = None) -> None:
        self.ffmpeg_path = ffmpeg_path
        self.app_root = app_root
        self._cancel_event = threading.Event()
        self._worker: Optional[threading.Thread] = None
        self._active_process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()

    @property
    def is_rendering(self) -> bool:
        return self._worker is not None and self._worker.is_alive()

    def render_async(
        self,
        job: RenderJob,
        progress_callback: Optional[ProgressCallback] = None,
        done_callback: Optional[Callable[[Optional[Path], Optional[Exception]], None]] = None,
    ) -> None:
        if self.is_rendering:
            raise RuntimeError("A render is already running.")
        self._cancel_event.clear()
        self._worker = threading.Thread(
            target=self._render_worker,
            args=(job, progress_callback, done_callback),
            name="RenderEngineWorker",
            daemon=True,
        )
        self._worker.start()

    def cancel(self) -> None:
        self._cancel_event.set()
        with self._lock:
            if self._active_process and self._active_process.poll() is None:
                self._active_process.terminate()

    def render_blocking(self, job: RenderJob, progress_callback: Optional[ProgressCallback] = None) -> Path:
        self.ffmpeg_path = ensure_tool(self.ffmpeg_path, self.app_root)
        with tempfile.TemporaryDirectory(prefix="dumperytpgen_") as tmp:
            tmpdir = Path(tmp)
            rendered_segments = self._render_segments(job, tmpdir, progress_callback)
            if self._cancel_event.is_set():
                raise RuntimeError("Render cancelled.")
            self._concat_segments(rendered_segments, job, progress_callback)
        return job.output_path

    def _render_worker(
        self,
        job: RenderJob,
        progress_callback: Optional[ProgressCallback],
        done_callback: Optional[Callable[[Optional[Path], Optional[Exception]], None]],
    ) -> None:
        try:
            output = self.render_blocking(job, progress_callback)
        except Exception as exc:  # noqa: BLE001 - user-facing error propagation
            LOGGER.exception("Render failed")
            if done_callback:
                done_callback(None, exc)
        else:
            if done_callback:
                done_callback(output, None)

    def _render_segments(
        self,
        job: RenderJob,
        tmpdir: Path,
        progress_callback: Optional[ProgressCallback],
    ) -> list[Path]:
        rendered: list[Path] = []
        total = max(len(job.clips), 1)
        for index, clip in enumerate(job.clips):
            if self._cancel_event.is_set():
                raise RuntimeError("Render cancelled.")
            segment = tmpdir / f"segment_{index:05d}.mp4"
            vf = ",".join(EffectChain.video_filters(clip.effects, job.width, job.height, job.fps))
            af = ",".join(EffectChain.audio_filters(clip.effects))
            command = [
                self.ffmpeg_path,
                "-y",
                "-ss",
                f"{clip.start:.3f}",
                "-t",
                f"{clip.duration:.3f}",
                "-i",
                str(clip.source),
                "-vf",
                vf,
                "-af",
                af,
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-shortest",
                str(segment),
            ]
            self._run(command)
            rendered.append(segment)
            if progress_callback:
                progress_callback((index + 1) / total * 80.0, f"Rendered clip {index + 1}/{total}")
        return rendered

    def _concat_segments(
        self,
        segments: list[Path],
        job: RenderJob,
        progress_callback: Optional[ProgressCallback],
    ) -> None:
        if not segments:
            raise RuntimeError("No clips were generated for rendering.")
        concat_file = segments[0].parent / "concat.txt"
        concat_file.write_text(
            "".join(f"file '{segment.as_posix()}'\n" for segment in segments),
            encoding="utf-8",
        )
        codec_args = self._codec_args(job.output_format)
        job.output_path.parent.mkdir(parents=True, exist_ok=True)
        needs_decoration = bool(job.overlays or job.audio_injections)
        concat_output = (
            segments[0].parent / f"base_timeline{job.output_path.suffix or '.mp4'}"
            if needs_decoration
            else job.output_path
        )
        command = [
            self.ffmpeg_path,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            *codec_args,
            str(concat_output),
        ]
        self._run(command)
        if needs_decoration:
            if progress_callback:
                progress_callback(90.0, "Applying overlays and audio injections")
            self._decorate_timeline(concat_output, job)
        if progress_callback:
            progress_callback(100.0, f"Wrote {job.output_path}")

    def _decorate_timeline(self, base_timeline: Path, job: RenderJob) -> None:
        """Apply random overlays and sound injections in one filter_complex pass."""

        command = [self.ffmpeg_path, "-y", "-i", str(base_timeline)]
        for overlay in job.overlays:
            if overlay.source.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
                command.extend(["-loop", "1", "-t", f"{overlay.duration:.3f}"])
            command.extend(["-i", str(overlay.source)])
        for injection in job.audio_injections:
            command.extend(["-i", str(injection.source)])

        filters: list[str] = []
        video_label = "[0:v]"
        for index, overlay in enumerate(job.overlays):
            input_index = index + 1
            radians = overlay.rotation_degrees * 3.141592653589793 / 180
            filters.append(
                f"[{input_index}:v]scale=iw*{overlay.scale:.3f}:-1,"
                f"rotate={radians:.6f}:c=none:ow=rotw(iw):oh=roth(ih),format=rgba[ov{index}]"
            )
            out_label = f"[v{index}]"
            filters.append(
                f"{video_label}[ov{index}]overlay={overlay.x}:{overlay.y}:"
                f"enable='between(t,{overlay.start:.3f},{overlay.start + overlay.duration:.3f})'{out_label}"
            )
            video_label = out_label

        audio_labels = ["[0:a]"]
        audio_offset = 1 + len(job.overlays)
        for index, injection in enumerate(job.audio_injections):
            input_index = audio_offset + index
            delay_ms = max(int(injection.start * 1000), 0)
            filters.append(
                f"[{input_index}:a]volume={injection.volume:.3f},"
                f"adelay={delay_ms}|{delay_ms},apad,atrim=0:{job.estimated_duration:.3f}[ainj{index}]"
            )
            audio_labels.append(f"[ainj{index}]")

        maps = ["-map", video_label if job.overlays else "0:v"]
        if job.audio_injections:
            filters.append(
                "".join(audio_labels)
                + f"amix=inputs={len(audio_labels)}:duration=first:dropout_transition=0,alimiter=limit=0.85[aout]"
            )
            maps.extend(["-map", "[aout]"])
        else:
            maps.extend(["-map", "0:a?"])

        if filters:
            command.extend(["-filter_complex", ";".join(filters)])
        command.extend([*maps, *self._codec_args(job.output_format), str(job.output_path)])
        self._run(command)

    def _run(self, command: list[str]) -> None:
        LOGGER.info("Running FFmpeg command: %s", " ".join(command))
        with self._lock:
            self._active_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                **subprocess_startup_options(),
            )
        stdout, stderr = self._active_process.communicate()
        if self._cancel_event.is_set():
            raise RuntimeError("Render cancelled.")
        if self._active_process.returncode != 0:
            raise RuntimeError(stderr.strip() or stdout.strip() or "FFmpeg command failed.")
        with self._lock:
            self._active_process = None

    def _codec_args(self, output_format: OutputFormat) -> list[str]:
        if output_format == OutputFormat.MP4_H265:
            return ["-c:v", "libx265", "-tag:v", "hvc1", "-c:a", "aac"]
        if output_format == OutputFormat.WEBM:
            return ["-c:v", "libvpx-vp9", "-b:v", "2M", "-c:a", "libopus"]
        return ["-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac"]
