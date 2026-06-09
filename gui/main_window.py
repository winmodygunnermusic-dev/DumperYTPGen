"""Tkinter user interface for DumperYTPGen."""
from __future__ import annotations

import logging
import queue
import tkinter as tk
from pathlib import Path
from typing import Optional
from tkinter import filedialog, messagebox, ttk

from core.auto_ytp_generator import AutoYTPGenerator
from core.models import MediaKind, OutputFormat, RenderJob
from library.manager import LibraryManager
from projects.project_manager import ProjectManager
from render.engine import RenderEngine

LOGGER = logging.getLogger(__name__)


class MainWindow(tk.Tk):
    """Main desktop window with library, generator, preview, and render controls."""

    def __init__(
        self,
        library_manager: LibraryManager,
        generator: AutoYTPGenerator,
        render_engine: RenderEngine,
        project_manager: ProjectManager,
    ) -> None:
        super().__init__()
        self.library_manager = library_manager
        self.generator = generator
        self.render_engine = render_engine
        self.project_manager = project_manager
        self.title("DumperYTPGen")
        self.geometry("1120x760")
        self.minsize(980, 680)

        self.status_var = tk.StringVar(value="Ready")
        self.output_var = tk.StringVar(value=str(Path.cwd() / "output" / "dumperytpgen.mp4"))
        self.duration_var = tk.StringVar(value="1 minute")
        self.format_var = tk.StringVar(value=OutputFormat.MP4_H264.value)
        self.old_school_var = tk.BooleanVar(value=True)
        self.progress_queue: queue.Queue[tuple[float, str]] = queue.Queue()
        self.current_job: Optional[RenderJob] = None

        self._build_widgets()
        self._load_library_safely()
        self.after(100, self._drain_progress_queue)

    def _build_widgets(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        notebook = ttk.Notebook(self)
        notebook.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        library_tab = ttk.Frame(notebook)
        generator_tab = ttk.Frame(notebook)
        preview_tab = ttk.Frame(notebook)
        notebook.add(library_tab, text="Media Library")
        notebook.add(generator_tab, text="Auto YTP Generator")
        notebook.add(preview_tab, text="Preview / Queue")

        self._build_library_tab(library_tab)
        self._build_generator_tab(generator_tab)
        self._build_preview_tab(preview_tab)

        status = ttk.Label(self, textvariable=self.status_var, anchor="w")
        status.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))

    def _build_library_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(1, weight=1)
        ttk.Label(
            parent,
            text=(
                "Configure source folders and/or add individual material files. "
                "Multi-file mode works for videos, images, sounds, music, memes, overlays, "
                "transitions, and characters."
            ),
        ).grid(row=0, column=0, columnspan=6, sticky="w", padx=10, pady=10)
        self.folder_vars: dict[MediaKind, tk.StringVar] = {}
        self.file_vars: dict[MediaKind, tk.StringVar] = {}
        for row, kind in enumerate(MediaKind, start=1):
            ttk.Label(parent, text=kind.value.replace("_", " ").title()).grid(
                row=row, column=0, sticky="w", padx=10, pady=4
            )
            folder_var = tk.StringVar()
            self.folder_vars[kind] = folder_var
            ttk.Entry(parent, textvariable=folder_var, width=32).grid(
                row=row, column=1, sticky="ew", padx=6, pady=4
            )
            ttk.Button(parent, text="Folder", command=lambda k=kind: self._choose_folder(k)).grid(
                row=row, column=2, padx=4, pady=4
            )
            file_var = tk.StringVar()
            self.file_vars[kind] = file_var
            ttk.Entry(parent, textvariable=file_var, width=32, state="readonly").grid(
                row=row, column=3, sticky="ew", padx=6, pady=4
            )
            ttk.Button(parent, text="Add Files", command=lambda k=kind: self._choose_files(k)).grid(
                row=row, column=4, padx=4, pady=4
            )
            ttk.Button(parent, text="Clear", command=lambda k=kind: self._clear_files(k)).grid(
                row=row, column=5, padx=(4, 10), pady=4
            )
        ttk.Button(parent, text="Scan Library", command=self._scan_library).grid(
            row=len(MediaKind) + 1, column=0, padx=10, pady=12, sticky="w"
        )
        self.library_summary = tk.Text(parent, height=12, wrap="word")
        self.library_summary.grid(
            row=len(MediaKind) + 2, column=0, columnspan=6, sticky="nsew", padx=10, pady=10
        )
        parent.columnconfigure(1, weight=1)
        parent.columnconfigure(3, weight=1)
        parent.rowconfigure(len(MediaKind) + 2, weight=1)

    def _build_generator_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(1, weight=1)
        ttk.Label(parent, text="Duration").grid(row=0, column=0, sticky="w", padx=10, pady=8)
        ttk.Combobox(
            parent,
            textvariable=self.duration_var,
            values=list(AutoYTPGenerator.DURATION_PRESETS),
            state="readonly",
        ).grid(row=0, column=1, sticky="w", padx=8, pady=8)

        ttk.Label(parent, text="Output Format").grid(row=1, column=0, sticky="w", padx=10, pady=8)
        ttk.Combobox(
            parent,
            textvariable=self.format_var,
            values=[item.value for item in OutputFormat],
            state="readonly",
        ).grid(row=1, column=1, sticky="w", padx=8, pady=8)

        ttk.Checkbutton(
            parent,
            text="Old School YTP Mode (2007-2012 visual spam, sentence-mix rhythm, loud jokes)",
            variable=self.old_school_var,
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=8)

        ttk.Label(parent, text="Output File").grid(row=3, column=0, sticky="w", padx=10, pady=8)
        ttk.Entry(parent, textvariable=self.output_var).grid(row=3, column=1, sticky="ew", padx=8, pady=8)
        ttk.Button(parent, text="Browse", command=self._choose_output).grid(row=3, column=2, padx=10)

        buttons = ttk.Frame(parent)
        buttons.grid(row=4, column=0, columnspan=3, sticky="w", padx=10, pady=14)
        ttk.Button(buttons, text="Generate Timeline", command=self._generate_timeline).grid(row=0, column=0, padx=4)
        ttk.Button(buttons, text="Render", command=self._render).grid(row=0, column=1, padx=4)
        ttk.Button(buttons, text="Cancel Render", command=self.render_engine.cancel).grid(row=0, column=2, padx=4)

        self.progress = ttk.Progressbar(parent, maximum=100)
        self.progress.grid(row=5, column=0, columnspan=3, sticky="ew", padx=10, pady=8)
        self.timeline_text = tk.Text(parent, height=22, wrap="none")
        self.timeline_text.grid(row=6, column=0, columnspan=3, sticky="nsew", padx=10, pady=10)
        parent.rowconfigure(6, weight=1)

    def _build_preview_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)
        ttk.Label(
            parent,
            text=(
                "Embedded playback is represented by render metadata for portability. "
                "Open the rendered file in your platform media player for full preview."
            ),
        ).grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.preview_text = tk.Text(parent, wrap="word")
        self.preview_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

    def _load_library_safely(self) -> None:
        try:
            self.library_manager.load()
        except Exception as exc:  # noqa: BLE001 - keep GUI bootable with bad JSON
            LOGGER.warning("Could not load library metadata: %s", exc)
        for kind, folder in self.library_manager.folders.items():
            self.folder_vars[kind].set(str(folder))
        for kind in MediaKind:
            self._refresh_file_var(kind)
        self._refresh_library_summary()

    def _choose_folder(self, kind: MediaKind) -> None:
        folder = filedialog.askdirectory(title=f"Select {kind.value} folder")
        if folder:
            self.folder_vars[kind].set(folder)
            self.library_manager.set_folder(kind, Path(folder))
            self.library_manager.save()

    def _choose_files(self, kind: MediaKind) -> None:
        filenames = filedialog.askopenfilenames(
            title=f"Add {kind.value} material files",
            filetypes=self._filetypes_for_kind(kind),
        )
        if filenames:
            self.library_manager.add_files(kind, [Path(filename) for filename in filenames])
            self.library_manager.save()
            self._refresh_file_var(kind)

    def _clear_files(self, kind: MediaKind) -> None:
        self.library_manager.clear_files(kind)
        self.library_manager.save()
        self._refresh_file_var(kind)

    def _refresh_file_var(self, kind: MediaKind) -> None:
        files = self.library_manager.files.get(kind, [])
        if not files:
            self.file_vars[kind].set("")
            return
        preview = "; ".join(path.name for path in files[:3])
        if len(files) > 3:
            preview = f"{preview}; +{len(files) - 3} more"
        self.file_vars[kind].set(preview)

    def _filetypes_for_kind(self, kind: MediaKind) -> list[tuple[str, str]]:
        video = " ".join(f"*{ext}" for ext in sorted(self.library_manager.VIDEO_EXTENSIONS))
        image = " ".join(f"*{ext}" for ext in sorted(self.library_manager.IMAGE_EXTENSIONS))
        audio = " ".join(f"*{ext}" for ext in sorted(self.library_manager.AUDIO_EXTENSIONS))
        if kind in {MediaKind.SOURCE_VIDEOS, MediaKind.MEME_CLIPS, MediaKind.TRANSITIONS}:
            return [("Video files", video), ("All files", "*.*")]
        if kind in {MediaKind.SOURCE_IMAGES, MediaKind.OVERLAYS, MediaKind.CHARACTERS}:
            return [("Image/video files", f"{image} {video}"), ("All files", "*.*")]
        if kind in {MediaKind.SOUND_EFFECTS, MediaKind.MUSIC}:
            return [("Audio/video files", f"{audio} {video}"), ("All files", "*.*")]
        return [("All files", "*.*")]

    def _choose_output(self) -> None:
        filename = filedialog.asksaveasfilename(
            title="Render output",
            defaultextension=".mp4",
            filetypes=[("MP4", "*.mp4"), ("WebM", "*.webm"), ("All files", "*.*")],
        )
        if filename:
            self.output_var.set(filename)

    def _scan_library(self) -> None:
        for kind, var in self.folder_vars.items():
            if var.get().strip():
                self.library_manager.set_folder(kind, Path(var.get()))
        try:
            self.library_manager.scan()
        except Exception as exc:  # noqa: BLE001 - GUI error dialog
            messagebox.showerror("Scan failed", str(exc))
            return
        self._refresh_library_summary()
        self.status_var.set("Library scanned and metadata saved.")

    def _refresh_library_summary(self) -> None:
        self.library_summary.delete("1.0", tk.END)
        for kind in MediaKind:
            direct_files = len(self.library_manager.files.get(kind, []))
            self.library_summary.insert(
                tk.END,
                f"{kind.value}: {len(self.library_manager.get_items(kind))} scanned items "
                f"({direct_files} direct files selected)\n",
            )

    def _generate_timeline(self) -> None:
        try:
            self.current_job = self.generator.build_job(
                self.duration_var.get(),
                Path(self.output_var.get()),
                OutputFormat(self.format_var.get()),
                self.old_school_var.get(),
            )
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Generation failed", str(exc))
            return
        self._show_job(self.current_job)
        self.project_manager.current_project["last_job"] = {
            "output_path": str(self.current_job.output_path),
            "clip_count": len(self.current_job.clips),
            "duration": self.current_job.estimated_duration,
        }
        self.project_manager.autosave()
        self.status_var.set("Timeline generated.")

    def _show_job(self, job: RenderJob) -> None:
        self.timeline_text.delete("1.0", tk.END)
        self.preview_text.delete("1.0", tk.END)
        cursor = 0.0
        for index, clip in enumerate(job.clips, start=1):
            self.timeline_text.insert(
                tk.END,
                f"{index:03d} {cursor:07.2f}s +{clip.duration:04.1f}s "
                f"{clip.source.name} effects={','.join(clip.effects)}\n",
            )
            cursor += clip.duration
        self.preview_text.insert(
            tk.END,
            f"Output: {job.output_path}\nDuration: {job.estimated_duration:.2f}s\n"
            f"Clips: {len(job.clips)}\nOverlays: {len(job.overlays)}\n"
            f"Audio injections: {len(job.audio_injections)}\nTransition style: {job.transition}\n",
        )

    def _render(self) -> None:
        if self.current_job is None:
            self._generate_timeline()
        if self.current_job is None:
            return
        try:
            self.render_engine.render_async(
                self.current_job,
                progress_callback=lambda value, msg: self.progress_queue.put((value, msg)),
                done_callback=self._render_done,
            )
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Render failed", str(exc))
            return
        self.status_var.set("Rendering...")

    def _render_done(self, output: Optional[Path], error: Optional[Exception]) -> None:
        if error:
            self.progress_queue.put((0.0, f"Render failed: {error}"))
        else:
            self.progress_queue.put((100.0, f"Render complete: {output}"))

    def _drain_progress_queue(self) -> None:
        while not self.progress_queue.empty():
            value, message = self.progress_queue.get_nowait()
            self.progress.configure(value=value)
            self.status_var.set(message)
        self.after(100, self._drain_progress_queue)
