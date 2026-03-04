"""Custom exceptions for ffmpeg_wrapper."""


class FFmpegError(Exception):
    """Raised when an ffmpeg command fails."""


class FFprobeError(Exception):
    """Raised when an ffprobe command fails."""


class FFmpegNotFoundError(FFmpegError):
    """Raised when the ffmpeg executable cannot be found."""


class FFprobeNotFoundError(FFprobeError):
    """Raised when the ffprobe executable cannot be found."""
