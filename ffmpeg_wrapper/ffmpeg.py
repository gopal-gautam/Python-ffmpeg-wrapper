"""Core FFmpeg wrapper providing a fluent, chainable Python API."""

import shutil
import subprocess
from typing import List, Optional, Union

from .exceptions import FFmpegError, FFmpegNotFoundError


class FFmpeg:
    """A fluent wrapper around the ``ffmpeg`` command-line tool.

    Build a pipeline by chaining method calls and execute it with
    :meth:`run`.

    Example usage::

        from ffmpeg_wrapper import FFmpeg

        # Simple format conversion
        FFmpeg().input("input.mp4").output("output.avi").run()

        # Trim a clip
        (
            FFmpeg()
            .input("input.mp4")
            .trim(start="00:00:05", end="00:00:15")
            .output("clip.mp4")
            .run()
        )

        # Extract audio
        FFmpeg().input("movie.mp4").extract_audio().output("audio.mp3").run()

        # Scale video
        FFmpeg().input("hd.mp4").scale(1280, 720).output("hd720.mp4").run()

        # Change video/audio codec
        (
            FFmpeg()
            .input("input.mkv")
            .video_codec("libx264")
            .audio_codec("aac")
            .output("output.mp4")
            .run()
        )
    """

    def __init__(self, ffmpeg_path: str = "ffmpeg", overwrite: bool = True):
        """Create an FFmpeg instance.

        Parameters
        ----------
        ffmpeg_path:
            Path or name of the ``ffmpeg`` executable (default ``"ffmpeg"``).
        overwrite:
            When ``True`` (default) the ``-y`` flag is passed so that output
            files are overwritten without prompting.
        """
        self._ffmpeg_path = ffmpeg_path
        self._overwrite = overwrite
        self._input_file: Optional[str] = None
        self._output_file: Optional[str] = None
        self._global_options: List[str] = []
        self._input_options: List[str] = []
        self._output_options: List[str] = []

    # ------------------------------------------------------------------
    # Input / output
    # ------------------------------------------------------------------

    def input(self, filepath: str, **options) -> "FFmpeg":
        """Set the input file.

        Parameters
        ----------
        filepath:
            Path to the input file.
        **options:
            Additional ffmpeg input options supplied as keyword arguments.
            Underscores in key names are converted to hyphens, e.g.
            ``ss="00:00:10"`` becomes ``-ss 00:00:10``.

        Returns
        -------
        FFmpeg
            The current instance (for chaining).
        """
        self._input_file = str(filepath)
        for key, value in options.items():
            self._input_options += [f"-{key.replace('_', '-')}", str(value)]
        return self

    def output(self, filepath: str, **options) -> "FFmpeg":
        """Set the output file.

        Parameters
        ----------
        filepath:
            Path for the output file.
        **options:
            Additional ffmpeg output options supplied as keyword arguments.
            Underscores in key names are converted to hyphens.

        Returns
        -------
        FFmpeg
            The current instance (for chaining).
        """
        self._output_file = str(filepath)
        for key, value in options.items():
            self._output_options += [f"-{key.replace('_', '-')}", str(value)]
        return self

    # ------------------------------------------------------------------
    # Common video/audio operations
    # ------------------------------------------------------------------

    def trim(
        self,
        start: Union[str, float, int] = 0,
        end: Optional[Union[str, float, int]] = None,
        duration: Optional[Union[str, float, int]] = None,
    ) -> "FFmpeg":
        """Trim the media to a time range.

        Provide either *end* (absolute timestamp) **or** *duration* (length
        of the clip), not both.

        Parameters
        ----------
        start:
            Start time (seconds or ``HH:MM:SS[.xxx]`` string).  Default 0.
        end:
            End time (seconds or timestamp string).
        duration:
            Duration of the output clip (seconds or timestamp string).

        Returns
        -------
        FFmpeg
            The current instance (for chaining).
        """
        if end is not None and duration is not None:
            raise ValueError("Provide either 'end' or 'duration', not both.")
        self._output_options += ["-ss", str(start)]
        if end is not None:
            self._output_options += ["-to", str(end)]
        elif duration is not None:
            self._output_options += ["-t", str(duration)]
        return self

    def extract_audio(self, no_video: bool = True) -> "FFmpeg":
        """Extract the audio stream (discard video by default).

        Parameters
        ----------
        no_video:
            When ``True`` (default) the ``-vn`` flag is added so that no
            video stream is written to the output.

        Returns
        -------
        FFmpeg
            The current instance (for chaining).
        """
        if no_video:
            self._output_options.append("-vn")
        return self

    def scale(
        self,
        width: Union[int, str] = -1,
        height: Union[int, str] = -1,
    ) -> "FFmpeg":
        """Scale the video.

        Use ``-1`` for a dimension to preserve the aspect ratio
        (e.g. ``scale(width=1280)`` keeps the correct height).

        Parameters
        ----------
        width:
            Target width in pixels, or ``-1`` to keep aspect ratio.
        height:
            Target height in pixels, or ``-1`` to keep aspect ratio.

        Returns
        -------
        FFmpeg
            The current instance (for chaining).
        """
        self._output_options += ["-vf", f"scale={width}:{height}"]
        return self

    def video_codec(self, codec: str) -> "FFmpeg":
        """Set the video codec.

        Parameters
        ----------
        codec:
            Codec name, e.g. ``"libx264"``, ``"libvpx-vp9"``, ``"copy"``.

        Returns
        -------
        FFmpeg
            The current instance (for chaining).
        """
        self._output_options += ["-c:v", codec]
        return self

    def audio_codec(self, codec: str) -> "FFmpeg":
        """Set the audio codec.

        Parameters
        ----------
        codec:
            Codec name, e.g. ``"aac"``, ``"libmp3lame"``, ``"copy"``.

        Returns
        -------
        FFmpeg
            The current instance (for chaining).
        """
        self._output_options += ["-c:a", codec]
        return self

    def video_bitrate(self, bitrate: str) -> "FFmpeg":
        """Set the video bitrate.

        Parameters
        ----------
        bitrate:
            Bitrate string, e.g. ``"1500k"`` or ``"2M"``.

        Returns
        -------
        FFmpeg
            The current instance (for chaining).
        """
        self._output_options += ["-b:v", bitrate]
        return self

    def audio_bitrate(self, bitrate: str) -> "FFmpeg":
        """Set the audio bitrate.

        Parameters
        ----------
        bitrate:
            Bitrate string, e.g. ``"128k"``.

        Returns
        -------
        FFmpeg
            The current instance (for chaining).
        """
        self._output_options += ["-b:a", bitrate]
        return self

    def fps(self, rate: Union[int, float, str]) -> "FFmpeg":
        """Set the output frame rate.

        Parameters
        ----------
        rate:
            Frames per second, e.g. ``24``, ``30``, ``"ntsc"``.

        Returns
        -------
        FFmpeg
            The current instance (for chaining).
        """
        self._output_options += ["-r", str(rate)]
        return self

    def audio_sample_rate(self, rate: int) -> "FFmpeg":
        """Set the audio sampling rate.

        Parameters
        ----------
        rate:
            Sample rate in Hz, e.g. ``44100``, ``48000``.

        Returns
        -------
        FFmpeg
            The current instance (for chaining).
        """
        self._output_options += ["-ar", str(rate)]
        return self

    def mute_audio(self) -> "FFmpeg":
        """Remove the audio stream from the output.

        Returns
        -------
        FFmpeg
            The current instance (for chaining).
        """
        self._output_options.append("-an")
        return self

    def mute_video(self) -> "FFmpeg":
        """Remove the video stream from the output.

        Returns
        -------
        FFmpeg
            The current instance (for chaining).
        """
        self._output_options.append("-vn")
        return self

    def output_format(self, fmt: str) -> "FFmpeg":
        """Force the output container format.

        Parameters
        ----------
        fmt:
            Format name, e.g. ``"mp4"``, ``"matroska"``, ``"webm"``.

        Returns
        -------
        FFmpeg
            The current instance (for chaining).
        """
        self._output_options += ["-f", fmt]
        return self

    def option(self, key: str, value: Optional[str] = None) -> "FFmpeg":
        """Add a raw output option.

        Provides an escape hatch for any ffmpeg option not covered by the
        high-level helpers.

        Parameters
        ----------
        key:
            Option name including the leading dash, e.g. ``"-crf"``.
        value:
            Option value, or ``None`` for flag-style options.

        Returns
        -------
        FFmpeg
            The current instance (for chaining).
        """
        self._output_options.append(key)
        if value is not None:
            self._output_options.append(str(value))
        return self

    # ------------------------------------------------------------------
    # Build and execute
    # ------------------------------------------------------------------

    def build(self) -> List[str]:
        """Return the ffmpeg command as a list of strings.

        Returns
        -------
        list[str]
            The full command ready for ``subprocess.run``.

        Raises
        ------
        ValueError
            If :meth:`input` or :meth:`output` have not been called yet.
        """
        if self._input_file is None:
            raise ValueError("No input file specified. Call .input() first.")
        if self._output_file is None:
            raise ValueError("No output file specified. Call .output() first.")

        cmd = [self._ffmpeg_path]
        if self._overwrite:
            cmd.append("-y")
        cmd += self._global_options
        cmd += self._input_options
        cmd += ["-i", self._input_file]
        cmd += self._output_options
        cmd.append(self._output_file)
        return cmd

    def run(
        self,
        capture_output: bool = False,
        quiet: bool = False,
    ) -> subprocess.CompletedProcess:
        """Execute the ffmpeg command.

        Parameters
        ----------
        capture_output:
            When ``True`` stdout and stderr are captured and returned in the
            :class:`subprocess.CompletedProcess` object rather than being
            printed to the terminal.
        quiet:
            When ``True`` the ``-loglevel quiet`` flag is added (suppresses
            all console output from ffmpeg).

        Returns
        -------
        subprocess.CompletedProcess
            The result of the subprocess call.

        Raises
        ------
        FFmpegNotFoundError
            If the ffmpeg executable is not found.
        FFmpegError
            If ffmpeg exits with a non-zero return code.
        """
        if shutil.which(self._ffmpeg_path) is None:
            raise FFmpegNotFoundError(
                f"'{self._ffmpeg_path}' executable not found. "
                "Please install ffmpeg and ensure it is on your PATH."
            )

        extra: List[str] = ["-loglevel", "quiet"] if quiet else []
        cmd = self.build()
        # Insert quiet flags right after the executable (and optional -y flag)
        if extra:
            insert_at = 2 if self._overwrite else 1
            cmd = cmd[:insert_at] + extra + cmd[insert_at:]

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE if capture_output else None,
                stderr=subprocess.PIPE if capture_output else None,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            stderr_msg = ""
            if exc.stderr:
                stderr_msg = exc.stderr.decode(errors="replace")
            raise FFmpegError(
                f"ffmpeg failed with return code {exc.returncode}:\n{stderr_msg}"
            ) from exc

        return result

    def __repr__(self) -> str:
        try:
            return f"FFmpeg({' '.join(self.build())})"
        except ValueError:
            return "FFmpeg(<incomplete – call .input() and .output()>)"
