"""Tests for the FFmpeg wrapper class."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from ffmpeg_wrapper import FFmpeg, FFmpegError, FFmpegNotFoundError


# ---------------------------------------------------------------------------
# build() – command construction
# ---------------------------------------------------------------------------


class TestBuild:
    def test_simple_conversion(self):
        cmd = FFmpeg().input("in.mp4").output("out.avi").build()
        assert cmd == ["ffmpeg", "-y", "-i", "in.mp4", "out.avi"]

    def test_overwrite_false(self):
        cmd = FFmpeg(overwrite=False).input("in.mp4").output("out.mp4").build()
        assert "-y" not in cmd

    def test_missing_input_raises(self):
        with pytest.raises(ValueError, match="No input file"):
            FFmpeg().output("out.mp4").build()

    def test_missing_output_raises(self):
        with pytest.raises(ValueError, match="No output file"):
            FFmpeg().input("in.mp4").build()

    def test_trim_with_end(self):
        cmd = (
            FFmpeg()
            .input("in.mp4")
            .trim(start="00:00:05", end="00:00:15")
            .output("out.mp4")
            .build()
        )
        assert "-ss" in cmd
        assert "00:00:05" in cmd
        assert "-to" in cmd
        assert "00:00:15" in cmd

    def test_trim_with_duration(self):
        cmd = (
            FFmpeg()
            .input("in.mp4")
            .trim(start=10, duration=30)
            .output("out.mp4")
            .build()
        )
        assert "-t" in cmd
        assert "30" in cmd

    def test_trim_both_end_and_duration_raises(self):
        with pytest.raises(ValueError):
            FFmpeg().input("in.mp4").trim(end="00:01:00", duration=60)

    def test_extract_audio(self):
        cmd = (
            FFmpeg()
            .input("in.mp4")
            .extract_audio()
            .output("out.mp3")
            .build()
        )
        assert "-vn" in cmd

    def test_extract_audio_keep_video(self):
        cmd = (
            FFmpeg()
            .input("in.mp4")
            .extract_audio(no_video=False)
            .output("out.mp3")
            .build()
        )
        assert "-vn" not in cmd

    def test_scale(self):
        cmd = (
            FFmpeg().input("in.mp4").scale(1280, 720).output("out.mp4").build()
        )
        assert "-vf" in cmd
        assert "scale=1280:720" in cmd

    def test_scale_keep_aspect(self):
        cmd = FFmpeg().input("in.mp4").scale(width=1280).output("out.mp4").build()
        assert "scale=1280:-1" in cmd

    def test_video_codec(self):
        cmd = (
            FFmpeg()
            .input("in.mp4")
            .video_codec("libx264")
            .output("out.mp4")
            .build()
        )
        assert "-c:v" in cmd
        assert "libx264" in cmd

    def test_audio_codec(self):
        cmd = (
            FFmpeg()
            .input("in.mp4")
            .audio_codec("aac")
            .output("out.mp4")
            .build()
        )
        assert "-c:a" in cmd
        assert "aac" in cmd

    def test_video_bitrate(self):
        cmd = (
            FFmpeg()
            .input("in.mp4")
            .video_bitrate("1500k")
            .output("out.mp4")
            .build()
        )
        assert "-b:v" in cmd
        assert "1500k" in cmd

    def test_audio_bitrate(self):
        cmd = (
            FFmpeg()
            .input("in.mp4")
            .audio_bitrate("128k")
            .output("out.mp4")
            .build()
        )
        assert "-b:a" in cmd
        assert "128k" in cmd

    def test_fps(self):
        cmd = FFmpeg().input("in.mp4").fps(30).output("out.mp4").build()
        assert "-r" in cmd
        assert "30" in cmd

    def test_audio_sample_rate(self):
        cmd = (
            FFmpeg()
            .input("in.mp4")
            .audio_sample_rate(44100)
            .output("out.mp3")
            .build()
        )
        assert "-ar" in cmd
        assert "44100" in cmd

    def test_mute_audio(self):
        cmd = FFmpeg().input("in.mp4").mute_audio().output("out.mp4").build()
        assert "-an" in cmd

    def test_mute_video(self):
        cmd = FFmpeg().input("in.mp4").mute_video().output("out.mp3").build()
        assert "-vn" in cmd

    def test_output_format(self):
        cmd = (
            FFmpeg()
            .input("in.mp4")
            .output_format("webm")
            .output("out.webm")
            .build()
        )
        assert "-f" in cmd
        assert "webm" in cmd

    def test_raw_option_with_value(self):
        cmd = (
            FFmpeg()
            .input("in.mp4")
            .option("-crf", "23")
            .output("out.mp4")
            .build()
        )
        assert "-crf" in cmd
        assert "23" in cmd

    def test_raw_option_flag(self):
        cmd = (
            FFmpeg()
            .input("in.mp4")
            .option("-nostdin")
            .output("out.mp4")
            .build()
        )
        assert "-nostdin" in cmd

    def test_input_options_from_kwargs(self):
        cmd = (
            FFmpeg()
            .input("in.mp4", ss="00:00:10")
            .output("out.mp4")
            .build()
        )
        assert "-ss" in cmd
        assert "00:00:10" in cmd
        # Input option must appear BEFORE -i
        ss_idx = cmd.index("-ss")
        i_idx = cmd.index("-i")
        assert ss_idx < i_idx

    def test_output_options_from_kwargs(self):
        cmd = (
            FFmpeg()
            .input("in.mp4")
            .output("out.mp4", vcodec="libx264")
            .build()
        )
        assert "-vcodec" in cmd
        assert "libx264" in cmd

    def test_chaining_returns_same_instance(self):
        f = FFmpeg()
        assert f.input("in.mp4") is f
        assert f.output("out.mp4") is f
        assert f.scale(640, 480) is f
        assert f.video_codec("copy") is f

    def test_repr_complete(self):
        r = repr(FFmpeg().input("in.mp4").output("out.mp4"))
        assert "ffmpeg" in r
        assert "in.mp4" in r

    def test_repr_incomplete(self):
        r = repr(FFmpeg())
        assert "incomplete" in r

    def test_custom_ffmpeg_path(self):
        cmd = FFmpeg(ffmpeg_path="/usr/local/bin/ffmpeg").input("a").output("b").build()
        assert cmd[0] == "/usr/local/bin/ffmpeg"


# ---------------------------------------------------------------------------
# run() – subprocess execution
# ---------------------------------------------------------------------------


class TestRun:
    def test_run_success(self):
        mock_result = MagicMock(spec=subprocess.CompletedProcess)
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"), patch(
            "subprocess.run", return_value=mock_result
        ) as mock_run:
            result = FFmpeg().input("in.mp4").output("out.avi").run()
            assert result is mock_result
            mock_run.assert_called_once()
            called_cmd = mock_run.call_args[0][0]
            assert called_cmd[0] == "ffmpeg"
            assert "in.mp4" in called_cmd
            assert "out.avi" in called_cmd

    def test_run_not_found_raises(self):
        with patch("shutil.which", return_value=None):
            with pytest.raises(FFmpegNotFoundError):
                FFmpeg().input("in.mp4").output("out.mp4").run()

    def test_run_nonzero_raises(self):
        exc = subprocess.CalledProcessError(1, "ffmpeg", stderr=b"error msg")
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"), patch(
            "subprocess.run", side_effect=exc
        ):
            with pytest.raises(FFmpegError, match="return code 1"):
                FFmpeg().input("in.mp4").output("out.mp4").run()

    def test_run_capture_output(self):
        mock_result = MagicMock(spec=subprocess.CompletedProcess)
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"), patch(
            "subprocess.run", return_value=mock_result
        ) as mock_run:
            FFmpeg().input("in.mp4").output("out.mp4").run(capture_output=True)
            _, kwargs = mock_run.call_args
            assert kwargs.get("stdout") == subprocess.PIPE
            assert kwargs.get("stderr") == subprocess.PIPE

    def test_run_quiet_adds_loglevel(self):
        mock_result = MagicMock(spec=subprocess.CompletedProcess)
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"), patch(
            "subprocess.run", return_value=mock_result
        ) as mock_run:
            FFmpeg().input("in.mp4").output("out.mp4").run(quiet=True)
            called_cmd = mock_run.call_args[0][0]
            assert "-loglevel" in called_cmd
            assert "quiet" in called_cmd

    def test_run_quiet_does_not_mutate_instance(self):
        """Calling run(quiet=True) must not permanently modify the instance."""
        mock_result = MagicMock(spec=subprocess.CompletedProcess)
        f = FFmpeg().input("in.mp4").output("out.mp4")
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"), patch(
            "subprocess.run", return_value=mock_result
        ) as mock_run:
            f.run(quiet=True)
            first_cmd = mock_run.call_args[0][0]
            assert "-loglevel" in first_cmd

            f.run(quiet=False)
            second_cmd = mock_run.call_args[0][0]
            assert "-loglevel" not in second_cmd
