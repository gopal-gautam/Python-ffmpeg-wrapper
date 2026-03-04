"""Tests for the probe() utility."""

import json
import subprocess
from unittest.mock import patch

import pytest

from ffmpeg_wrapper import FFprobeError, FFprobeNotFoundError, probe


class TestProbe:
    def test_returns_parsed_json(self):
        payload = {"format": {"filename": "test.mp4"}, "streams": []}
        mock_result = type(
            "CP",
            (),
            {"stdout": json.dumps(payload).encode(), "returncode": 0},
        )()
        with patch("shutil.which", return_value="/usr/bin/ffprobe"), patch(
            "subprocess.run", return_value=mock_result
        ):
            info = probe("test.mp4")
        assert info == payload

    def test_not_found_raises(self):
        with patch("shutil.which", return_value=None):
            with pytest.raises(FFprobeNotFoundError):
                probe("test.mp4")

    def test_nonzero_raises(self):
        exc = subprocess.CalledProcessError(1, "ffprobe", stderr=b"err")
        with patch("shutil.which", return_value="/usr/bin/ffprobe"), patch(
            "subprocess.run", side_effect=exc
        ):
            with pytest.raises(FFprobeError, match="return code 1"):
                probe("test.mp4")

    def test_custom_ffprobe_path(self):
        payload = {"format": {}, "streams": []}
        mock_result = type(
            "CP",
            (),
            {"stdout": json.dumps(payload).encode(), "returncode": 0},
        )()
        with patch("shutil.which", return_value="/custom/ffprobe"), patch(
            "subprocess.run", return_value=mock_result
        ) as mock_run:
            probe("test.mp4", ffprobe_path="/custom/ffprobe")
            called_cmd = mock_run.call_args[0][0]
            assert called_cmd[0] == "/custom/ffprobe"
