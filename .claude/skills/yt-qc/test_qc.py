#!/usr/bin/env python3
"""Offline tests for qc.py - no network, no credentials. Builds tiny MP4s with the local ffmpeg
and skips those cases if ffmpeg/ffprobe are missing.

    python3 test_qc.py
"""
import io, json, os, shutil, subprocess, sys, tempfile, unittest
from contextlib import redirect_stdout
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import qc

HAVE_FF = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
SMALL = ["--width", "320", "--height", "180"]


def run(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = qc.main(argv)
    return code, json.loads(buf.getvalue())


def status(report, cid):
    return next(c["status"] for c in report["checks"] if c["id"] == cid)


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)

    def make(self, name, seconds=2, size="320x180", fps=30, audio=True, vcodec="libx264", extra=(),
             src="color=c=blue"):
        p = os.path.join(self.dir, name)
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"{src}{':' if '=' in src else '='}s={size}:r={fps}:d={seconds}"]
        if audio:
            cmd += ["-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo", "-t", str(seconds), "-c:a", "aac"]
        cmd += ["-c:v", vcodec, "-pix_fmt", "yuv420p", *extra, p]
        subprocess.run(cmd, check=True)
        return p


@unittest.skipUnless(HAVE_FF, "ffmpeg/ffprobe not installed")
class QC(Base):
    def test_good_file_passes(self):
        p = self.make("ok.mp4")
        code, d = run([p, *SMALL, "--expected-duration", "2"])
        self.assertEqual((code, d["result"]), (0, "PASS"), d)
        self.assertEqual(d["summary"]["resolution"], "320x180")
        for cid in ("video_stream", "audio_stream", "frame_rate", "video_codec", "audio_codec",
                    "duration_matches_timeline", "streams_aligned", "full_decode"):
            self.assertEqual(status(d, cid), "pass", cid)

    def test_defaults_are_1080p30(self):
        code, d = run([self.make("ok.mp4")])
        self.assertEqual((code, status(d, "resolution")), (1, "fail"))

    def test_missing_file(self):
        code, d = run([os.path.join(self.dir, "nope.mp4")])
        self.assertEqual((code, d["result"], status(d, "file_exists")), (1, "FAIL", "fail"))

    def test_not_a_video(self):
        p = os.path.join(self.dir, "x.mp4")
        with open(p, "w") as f: f.write("hello")
        code, d = run([p])
        self.assertEqual((code, status(d, "container_readable")), (1, "fail"))

    def test_no_audio(self):
        code, d = run([self.make("silent.mp4", audio=False), *SMALL])
        self.assertEqual((code, status(d, "audio_stream")), (1, "fail"))

    def test_wrong_fps_codec_duration(self):
        p = self.make("w.mp4", fps=25, vcodec="mpeg4")
        code, d = run([p, *SMALL, "--expected-duration", "5"])
        self.assertEqual(code, 1)
        for cid in ("frame_rate", "video_codec", "duration_matches_timeline"):
            self.assertEqual(status(d, cid), "fail", cid)

    def test_truncated_file_fails(self):
        p = self.make("full.mp4", seconds=3, extra=("-movflags", "+faststart"))
        t = os.path.join(self.dir, "trunc.mp4")
        with open(p, "rb") as f, open(t, "wb") as g:
            g.write(f.read()[: os.path.getsize(p) // 2])
        code, d = run([t, *SMALL, "--expected-duration", "3"])
        self.assertEqual((code, d["result"]), (1, "FAIL"))
        failed = {c["id"] for c in d["checks"] if c["status"] == "fail"}
        self.assertTrue(failed & {"container_readable", "full_decode", "streams_aligned"}, failed)

    def test_truncated_mid_data_fails_decode(self):
        p = self.make("busy.mp4", seconds=4, src="testsrc2", extra=("-movflags", "+faststart"))
        t = os.path.join(self.dir, "cut.mp4")
        with open(p, "rb") as f, open(t, "wb") as g:
            g.write(f.read()[: os.path.getsize(p) * 6 // 10])
        code, d = run([t, *SMALL, "--expected-duration", "4"])
        self.assertEqual((code, status(d, "container_readable"), status(d, "full_decode")),
                         (1, "pass", "fail"))

    def test_size_limit(self):
        code, d = run([self.make("ok.mp4"), *SMALL, "--max-mb", "0.001"])
        self.assertEqual((code, status(d, "file_size")), (1, "fail"))

    def test_quick_skips_decode(self):
        code, d = run([self.make("ok.mp4"), *SMALL, "--quick"])
        self.assertEqual((code, status(d, "full_decode")), (0, "skip"))

    def test_expected_duration_from_timeline(self):
        from PIL import Image
        Image.new("RGB", (64, 36)).save(os.path.join(self.dir, "a.png"))
        tl = os.path.join(self.dir, "timeline.json")
        with open(tl, "w") as f:
            json.dump({"version": 1, "clips": [{"type": "image", "src": "a.png", "duration": 2}]}, f)
        code, d = run([self.make("ok.mp4"), *SMALL, "--timeline", tl])
        self.assertEqual((code, d["summary"]["expected_duration"]), (0, 2.0))


class Args(Base):
    def test_bad_args_are_json(self):
        for argv in (["a.mp4", "--expected-duration", "x"], ["a.mp4", "--fps", "nan"],
                     ["a.mp4", "--width"], ["a.mp4", "b.mp4"], ["a.mp4", "--bogus"],
                     ["a.mp4", "--timeline", "t.json", "--expected-duration", "1"]):
            code, d = run(argv)
            self.assertEqual((code, d["result"]), (2, "ERROR"), argv)

    def test_missing_ffprobe_is_json(self):
        p = os.path.join(self.dir, "x.mp4")
        with open(p, "w") as f: f.write("x")
        with mock.patch.object(qc.subprocess, "run", side_effect=FileNotFoundError()):
            code, d = run([p])
        self.assertEqual(code, 2); self.assertIn("not installed", d["error"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
