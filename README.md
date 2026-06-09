# DumperYTPGen

DumperYTPGen is a cross-platform Python 3.8+ Tkinter desktop application that automatically generates classic YouTube Poop (YTP)-style edits from local media libraries. It uses **FFmpeg** and **FFprobe** through `subprocess` for all video/audio processing.

## Features

- Media library folders and multi-file material selection for source videos, images, sounds, music, meme clips, overlays, transitions, and characters.
- FFprobe-powered video scanning and random clip generation.
- Classic YTP effect chains including speed changes, reverse, stutter, zoom spam, shake, hue/saturation/contrast boosts, freeze frames, audio chopping, pitch shifting, and datamosh-style simulation.
- Random overlays and sound injections.
- Keymate timeline marker presets for timestamp-triggered effects, overlays, sounds, and transitions.
- Dance music generation helpers with FFprobe audio analysis and beat-grid estimation.
- Thread-safe render engine with progress callbacks and cancellation.
- Tkinter GUI with project/library tabs, generator controls, preview metadata, and render queue.

## Requirements

- Python 3.8+ (Python 3.8.x is supported for Windows 8.1 deployments)
- FFmpeg and FFprobe available on `PATH`
- Tkinter (bundled with most Python distributions; install `python3-tk` on some Linux distros)

## Run

```bash
python -m app.main
```

## Material Multi-File Mode

Each media category can use a folder, individual files, or both. In the Media Library tab, use **Folder** for recursive folder scanning and **Add Files** to append multiple selected material files for videos, images, sounds, music, meme clips, overlays, transitions, or characters. Direct file selections are saved in the library metadata JSON alongside scanned items.

## Notes

This project intentionally avoids MoviePy and NumPy. Generated filter graphs are based on FFmpeg filters and subprocess execution.

## Windows 8.1 Support

DumperYTPGen is designed to run on Windows 8.1 with Python 3.8.x, Tkinter, and FFmpeg/FFprobe. To keep legacy Windows support practical:

- The app uses only Tkinter and the Python standard library; there are no MoviePy, NumPy, Windows Store, or Windows 10-only API dependencies.
- FFmpeg and FFprobe may be installed on `PATH`, or copied next to the app as `assets/bin/ffmpeg.exe` and `assets/bin/ffprobe.exe`.
- A Windows 8.1-specific bundle folder is also supported: `assets/bin/win8.1/ffmpeg.exe` and `assets/bin/win8.1/ffprobe.exe`.
- Subprocess calls hide FFmpeg/FFprobe console windows using Win32 flags that are available on Windows 8.1.

For Windows 8.1 deployments, use Python 3.8.x and a Windows 8.1-compatible FFmpeg build; newer Python runtimes may require newer Windows APIs.
