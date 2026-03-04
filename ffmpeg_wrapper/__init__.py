"""ffmpeg_wrapper – A fluent Python wrapper for the ffmpeg command-line tool."""

from .exceptions import (
    FFmpegError,
    FFmpegNotFoundError,
    FFprobeError,
    FFprobeNotFoundError,
)
from .ffmpeg import FFmpeg
from .probe import probe

__all__ = [
    "FFmpeg",
    "probe",
    "FFmpegError",
    "FFmpegNotFoundError",
    "FFprobeError",
    "FFprobeNotFoundError",
]

__version__ = "0.1.0"
