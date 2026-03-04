"""Media probing utilities using ffprobe."""

import json
import shutil
import subprocess

from .exceptions import FFprobeError, FFprobeNotFoundError


def probe(filepath, ffprobe_path="ffprobe"):
    """Return a dict of media information for *filepath* using ffprobe.

    Parameters
    ----------
    filepath:
        Path to the media file to inspect.
    ffprobe_path:
        Path or name of the ffprobe executable (default ``"ffprobe"``).

    Returns
    -------
    dict
        Parsed JSON output from ``ffprobe``.

    Raises
    ------
    FFprobeNotFoundError
        If the ffprobe executable is not found.
    FFprobeError
        If ffprobe exits with a non-zero return code.
    """
    if shutil.which(ffprobe_path) is None:
        raise FFprobeNotFoundError(
            f"'{ffprobe_path}' executable not found. "
            "Please install ffmpeg/ffprobe and ensure it is on your PATH."
        )

    cmd = [
        ffprobe_path,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(filepath),
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise FFprobeError(
            f"ffprobe failed with return code {exc.returncode}:\n"
            + exc.stderr.decode(errors="replace")
        ) from exc

    return json.loads(result.stdout.decode())
