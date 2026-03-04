# Python-ffmpeg-wrapper

A lightweight, fluent Python wrapper for the [ffmpeg](https://ffmpeg.org/) command-line tool.
Build complex ffmpeg pipelines using simple, chainable Python method calls — no string wrangling required.

## Requirements

* Python 3.8+
* [ffmpeg](https://ffmpeg.org/download.html) installed and available on your system `PATH`

## Installation

```bash
pip install ffmpeg-wrapper
```

> **Note:** The package requires ffmpeg to be installed separately.
> See the [official ffmpeg download page](https://ffmpeg.org/download.html) for instructions.

## Quick start

```python
from ffmpeg_wrapper import FFmpeg, probe

# ── Convert a video ──────────────────────────────────────────────────────────
FFmpeg().input("input.mp4").output("output.avi").run()

# ── Trim a clip ───────────────────────────────────────────────────────────────
(
    FFmpeg()
    .input("input.mp4")
    .trim(start="00:00:05", end="00:00:15")
    .output("clip.mp4")
    .run()
)

# ── Extract audio ─────────────────────────────────────────────────────────────
FFmpeg().input("movie.mp4").extract_audio().output("audio.mp3").run()

# ── Scale / resize ────────────────────────────────────────────────────────────
FFmpeg().input("4k.mp4").scale(1920, 1080).output("1080p.mp4").run()

# ── Change codec and bitrate ──────────────────────────────────────────────────
(
    FFmpeg()
    .input("input.mkv")
    .video_codec("libx264")
    .video_bitrate("1500k")
    .audio_codec("aac")
    .audio_bitrate("128k")
    .output("output.mp4")
    .run()
)

# ── Inspect a file (ffprobe) ──────────────────────────────────────────────────
info = probe("video.mp4")
print(info["format"]["duration"])
```

## API reference

### `FFmpeg(ffmpeg_path="ffmpeg", overwrite=True)`

| Method | Description |
|---|---|
| `.input(filepath, **options)` | Set the input file. Keyword args become `-key value` input options. |
| `.output(filepath, **options)` | Set the output file. Keyword args become `-key value` output options. |
| `.trim(start=0, end=None, duration=None)` | Trim the clip to a time range. |
| `.extract_audio(no_video=True)` | Extract the audio stream (`-vn`). |
| `.scale(width=-1, height=-1)` | Scale the video (`-vf scale=W:H`). |
| `.video_codec(codec)` | Set the video codec (`-c:v`). |
| `.audio_codec(codec)` | Set the audio codec (`-c:a`). |
| `.video_bitrate(bitrate)` | Set the video bitrate (`-b:v`). |
| `.audio_bitrate(bitrate)` | Set the audio bitrate (`-b:a`). |
| `.fps(rate)` | Set the output frame rate (`-r`). |
| `.audio_sample_rate(rate)` | Set the audio sample rate (`-ar`). |
| `.mute_audio()` | Drop the audio stream (`-an`). |
| `.mute_video()` | Drop the video stream (`-vn`). |
| `.output_format(fmt)` | Force the output container format (`-f`). |
| `.option(key, value=None)` | Add any raw ffmpeg output option. |
| `.build()` | Return the command as a `list[str]` without running it. |
| `.run(capture_output=False, quiet=False)` | Execute the command and return a `subprocess.CompletedProcess`. |

### `probe(filepath, ffprobe_path="ffprobe")`

Returns a dictionary of media information for `filepath` (format and all streams) using `ffprobe`.

## Publishing to PyPI

```bash
# Build the distribution
python -m build

# Upload to PyPI (requires a PyPI account and API token)
python -m twine upload dist/*
```

## License

[MIT](LICENSE)
