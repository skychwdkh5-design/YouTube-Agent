#!/usr/bin/env python3
"""Offline tests for render.py - no network, no credentials. Uses the local ffmpeg/ffprobe for the
small real renders (320x180, ultrafast) and skips those if the binaries are missing.

    python3 test_render.py
"""
import io, json, os, shutil, sys, tempfile, unittest
from contextlib import redirect_stdout
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as r

HAVE_FF = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
SMALL = {"width": 320, "height": 180, "preset": "ultrafast"}


def run(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = r.main(argv)
    return code, json.loads(buf.getvalue())


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)

    def img(self, name, size=(400, 300), color=(200, 40, 40)):
        from PIL import Image
        Image.new("RGB", size, color).save(os.path.join(self.dir, name))
        return name

    def timeline(self, clips, output=SMALL, **extra):
        p = os.path.join(self.dir, "timeline.json")
        with open(p, "w") as f:
            json.dump({"version": 1, "output": output, "clips": clips, **extra}, f)
        return p

    def out(self, name="final.mp4"):
        return os.path.join(self.dir, name)


@unittest.skipUnless(HAVE_FF, "ffmpeg/ffprobe not installed")
class Validation(Base):
    def test_requires_confirm_and_returns_plan(self):
        tl = self.timeline([{"type": "image", "src": self.img("a.png"), "duration": 2}])
        code, d = run(["--timeline", tl, "--output", self.out()])
        self.assertEqual((code, d["status"]), (2, "confirm_required"))
        self.assertEqual(d["plan"]["expected_duration"], 2.0)
        self.assertFalse(os.path.exists(self.out()))

    def test_missing_file(self):
        tl = self.timeline([{"type": "image", "src": "nope.jpg", "duration": 2}])
        code, d = run(["--timeline", tl, "--output", self.out(), "--confirm"])
        self.assertEqual(code, 2); self.assertIn("not found", d["error"])

    def test_path_escape_and_url_rejected(self):
        outside = tempfile.NamedTemporaryFile(suffix=".png", delete=False); outside.close()
        self.addCleanup(os.remove, outside.name)
        for src in ("../" + os.path.basename(outside.name), outside.name, "https://x/y.jpg"):
            tl = self.timeline([{"type": "image", "src": src, "duration": 2}])
            code, d = run(["--timeline", tl, "--output", self.out(), "--confirm"])
            self.assertEqual(code, 2, src)
            self.assertTrue("outside the media root" in d["error"] or "URL" in d["error"], d)

    def test_unsupported_media(self):
        with open(os.path.join(self.dir, "fake.jpg"), "w") as f: f.write("not an image")
        with open(os.path.join(self.dir, "a.gif"), "wb") as f: f.write(b"GIF89a")
        for src, msg in (("fake.jpg", "not a"), ("a.gif", "unsupported file type")):
            tl = self.timeline([{"type": "image", "src": src, "duration": 2}])
            code, d = run(["--timeline", tl, "--output", self.out(), "--confirm"])
            self.assertEqual(code, 2); self.assertIn(msg, d["error"])

    def test_future_tracks_rejected_not_dropped(self):
        a = self.img("a.png")
        for extra, clip in (({"audio": {"voice": [{"src": "v.wav"}]}}, {}),
                            ({"subtitles": {"src": "s.srt"}}, {}),
                            ({}, {"type": "video"})):
            tl = self.timeline([dict({"type": "image", "src": a, "duration": 2}, **clip)], **extra)
            code, d = run(["--timeline", tl, "--output", self.out(), "--confirm"])
            self.assertEqual((code, d["status"]), (2, "unsupported"), extra or clip)

    def test_bad_values(self):
        a = self.img("a.png")
        cases = [{"duration": "x"}, {"duration": 0}, {"duration": float("nan")},
                 {"motion": {"type": "kenburns", "zoom": [1.0, 9]}}, {"motion": {"pan": "diagonal"}},
                 {"fit": "stretch"}, {"bogus": 1}]
        for c in cases:
            tl = self.timeline([dict({"type": "image", "src": a, "duration": 2}, **c)])
            code, d = run(["--timeline", tl, "--output", self.out(), "--confirm"])
            self.assertEqual((code, d["status"]), (2, "error"), c)
        for o in ({"width": 321, "height": 180}, {"fps": 29}, {"video_codec": "vp9"}):
            tl = self.timeline([{"type": "image", "src": a, "duration": 2}], output=dict(SMALL, **o))
            self.assertEqual(run(["--timeline", tl, "--confirm", "--output", self.out()])[0], 2, o)
        code, d = run(["--timeline", tl, "--max-output-mb", "x"])
        self.assertEqual(code, 2); self.assertIn("expects a number", d["error"])

    def test_transition_longer_than_clip(self):
        a = self.img("a.png")
        tl = self.timeline([{"type": "image", "src": a, "duration": 1,
                             "transition": {"type": "crossfade", "duration": 1.5}},
                            {"type": "image", "src": a, "duration": 1}])
        code, d = run(["--timeline", tl, "--output", self.out(), "--confirm"])
        self.assertEqual(code, 2); self.assertIn("transition", d["error"])

    def test_limits(self):
        a = self.img("a.png")
        tl = self.timeline([{"type": "image", "src": a, "duration": 20}])
        self.assertIn("max-duration", run(["--timeline", tl, "--max-duration", "10"])[1]["error"])
        self.assertIn("max-input-mb", run(["--timeline", tl, "--max-input-mb", "0.0001"])[1]["error"])

    def test_extreme_aspect_needs_contain(self):
        tl = self.timeline([{"type": "image", "src": self.img("thin.png", (2000, 20)), "duration": 1}])
        code, d = run(["--timeline", tl])
        self.assertIn("contain", d["error"])
        tl = self.timeline([{"type": "image", "src": "thin.png", "duration": 1, "fit": "contain"}])
        self.assertEqual(run(["--timeline", tl])[1]["status"], "confirm_required")

    def test_expected_duration_math(self):
        a = self.img("a.png")
        tl = self.timeline([{"type": "image", "src": a, "duration": 3,
                             "transition": {"type": "crossfade", "duration": 1}},
                            {"type": "image", "src": a, "duration": 3},
                            {"type": "image", "src": a, "duration": 2}])
        self.assertEqual(r.expected_duration(tl), 7.0)


@unittest.skipUnless(HAVE_FF, "ffmpeg/ffprobe not installed")
class Rendering(Base):
    def probe(self, path):
        return r.ffprobe_json(path)

    def test_render_multi_image_exact(self):
        a, b = self.img("a.png"), self.img("odd.jpg", (37, 101), (30, 200, 30))
        tl = self.timeline([
            {"type": "landsat", "src": a, "duration": 1.5, "credit": "USGS",
             "motion": {"type": "kenburns", "zoom": [1.0, 1.3], "pan": "left_to_right"},
             "transition": {"type": "crossfade", "duration": 0.5}},
            {"type": "image", "src": b, "duration": 1.2, "fit": "contain"},
            {"type": "image", "src": a, "duration": 1, "motion": {"type": "static"}}])
        code, d = run(["--timeline", tl, "--output", self.out(), "--confirm"])
        self.assertEqual((code, d["status"]), (0, "ok"), d)
        self.assertEqual((d["duration"], d["expected_duration"]), (3.2, 3.2))
        p = self.probe(self.out())
        v = [s for s in p["streams"] if s["codec_type"] == "video"][0]
        au = [s for s in p["streams"] if s["codec_type"] == "audio"][0]
        self.assertEqual((v["codec_name"], v["width"], v["height"], v["avg_frame_rate"], v["nb_frames"]),
                         ("h264", 320, 180, "30/1", "96"))
        self.assertEqual((au["codec_name"], au["channels"]), ("aac", 2))
        self.assertEqual([f for f in os.listdir(self.dir) if "partial" in f], [])

    def test_deterministic(self):
        tl = self.timeline([{"type": "image", "src": self.img("a.png"), "duration": 1}])
        h = [run(["--timeline", tl, "--output", self.out(f"{i}.mp4"), "--confirm"])[1]["sha256"]
             for i in (1, 2)]
        self.assertEqual(h[0], h[1])

    def test_no_overwrite_without_flag(self):
        tl = self.timeline([{"type": "image", "src": self.img("a.png"), "duration": 1}])
        with open(self.out(), "w") as f: f.write("keep me")
        code, d = run(["--timeline", tl, "--output", self.out(), "--confirm"])
        self.assertEqual((code, d["status"]), (2, "exists"))
        with open(self.out()) as f: self.assertEqual(f.read(), "keep me")
        code, d = run(["--timeline", tl, "--output", self.out(), "--confirm", "--overwrite"])
        self.assertEqual(code, 0); self.assertGreater(os.path.getsize(self.out()), 1000)

    def test_failed_render_leaves_no_output(self):
        tl = self.timeline([{"type": "image", "src": self.img("a.png"), "duration": 1}])
        real_run = r._run

        def failing(cmd, timeout):
            if cmd[0] == "ffmpeg":
                with open(cmd[-1], "wb") as f: f.write(b"half a file")
                return mock.Mock(returncode=1, stderr="boom", stdout="")
            return real_run(cmd, timeout)
        with mock.patch.object(r, "_run", failing):
            code, d = run(["--timeline", tl, "--output", self.out(), "--confirm"])
        self.assertEqual(code, 2); self.assertIn("ffmpeg failed", d["error"])
        self.assertEqual(sorted(os.listdir(self.dir)), ["a.png", "timeline.json"])

    def test_output_size_limit_discards_file(self):
        tl = self.timeline([{"type": "image", "src": self.img("a.png"), "duration": 2}])
        code, d = run(["--timeline", tl, "--output", self.out(), "--confirm", "--max-output-mb", "0.001"])
        self.assertEqual(code, 2)
        self.assertFalse(os.path.exists(self.out()))
        self.assertEqual([f for f in os.listdir(self.dir) if f.endswith(".mp4")], [])

    def test_output_cannot_be_a_source(self):
        tl = self.timeline([{"type": "image", "src": self.img("a.png"), "duration": 1}])
        code, d = run(["--timeline", tl, "--output", os.path.join(self.dir, "a.png"), "--confirm"])
        self.assertEqual(code, 2)


class NoFFmpeg(Base):
    def test_missing_binary_is_json(self):
        with mock.patch.object(r.subprocess, "run", side_effect=FileNotFoundError()):
            with open(os.path.join(self.dir, "a.png"), "wb") as f: f.write(b"\x89PNG")
            tl = self.timeline([{"type": "image", "src": "a.png", "duration": 1}])
            code, d = run(["--timeline", tl])
        self.assertEqual(code, 2); self.assertIn("not installed", d["error"])

    def test_unreadable_timeline(self):
        p = os.path.join(self.dir, "bad.json")
        with open(p, "w") as f: f.write("{nope")
        self.assertEqual(run(["--timeline", p])[0], 2)
        self.assertIn("not found", run(["--timeline", p + "x"])[1]["error"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
