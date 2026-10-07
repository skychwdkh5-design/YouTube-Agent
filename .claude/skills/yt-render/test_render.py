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
        for extra, clip in (({"audio": {"music": [{"src": "m.wav"}]}}, {}),
                            ({"audio": {"sfx": [{"src": "s.wav"}]}}, {}),
                            ({"overlays": [{"type": "text"}]}, {}),
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

        def failing(cmd, timeout, cwd=None):
            if cmd[0] == "ffmpeg":
                with open(cmd[-1], "wb") as f: f.write(b"half a file")
                return mock.Mock(returncode=1, stderr="boom", stdout="")
            return real_run(cmd, timeout, cwd)
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


# --- narration, subtitles, credit ----------------------------------------------------------------

def tone_wav(path, seconds, rate=44100, click_at=None):
    """Silence with an optional 50 ms full-scale burst at click_at - a timing probe."""
    import wave, struct, math as m
    n = int(seconds * rate)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        frames = bytearray()
        for i in range(n):
            t = i / rate
            on = click_at is not None and click_at <= t < click_at + 0.05
            v = int(20000 * m.sin(2 * m.pi * 1000 * t)) if on else 0
            frames += struct.pack("<h", v)
        w.writeframes(bytes(frames))


def onset(path, rate=48000):
    """First sample above -20 dBFS in the rendered audio, in seconds."""
    import subprocess as sp, struct
    raw = sp.run(["ffmpeg", "-v", "error", "-i", path, "-map", "0:a", "-ac", "1", "-ar", str(rate),
                  "-f", "s16le", "-"], capture_output=True, check=True).stdout
    vals = struct.unpack(f"<{len(raw) // 2}h", raw)
    for i, v in enumerate(vals):
        if abs(v) > 3277:
            return i / rate
    return None


SRT = """1
00:00:00,200 --> 00:00:01,400
Hello there, this is

2
00:00:01,400 --> 00:00:02,600
a subtitle test.
"""


@unittest.skipUnless(HAVE_FF, "ffmpeg/ffprobe not installed")
class Narration(Base):
    def setUp(self):
        super().setUp()
        self.a = self.img("a.png")

    def voice_meta(self, wav, **over):
        meta = {"schema": "yt-voice/1", "voice_name": "Adam", "voice_id": "pNInz6obpgDQGcFmaJgB",
                "audio_sha256": r._sha256(os.path.join(self.dir, wav)),
                "duration": r.wave_duration(os.path.join(self.dir, wav)) if hasattr(r, "wave_duration") else None}
        meta.update(over)
        with open(os.path.join(self.dir, "n.voice.json"), "w") as f:
            json.dump(meta, f)
        return "n.voice.json"

    def test_narration_timing_is_exact(self):
        for loud in (False, True):
            tone_wav(os.path.join(self.dir, "n.wav"), 2.0, click_at=0.5)
            tl = self.timeline([{"type": "image", "src": self.a, "duration": 3}],
                               audio={"voice": [{"src": "n.wav", "start": 0.25, "normalize": loud}]})
            out = self.out(f"v{int(loud)}.mp4")
            code, d = run(["--timeline", tl, "--output", out, "--confirm"])
            self.assertEqual((code, d["status"]), (0, "ok"), d)
            self.assertEqual(d["narration"]["start"], 0.25)
            # burst at 0.5 s in the narration + 0.25 s start = 0.75 s in the video
            self.assertAlmostEqual(onset(out), 0.75, delta=0.005)
            if loud:
                self.assertNotEqual(d["narration"]["gain_db"], 0.0)
            self.assertEqual(d["duration"], 3.0)

    def test_narration_never_cut(self):
        tone_wav(os.path.join(self.dir, "n.wav"), 3.0)
        tl = self.timeline([{"type": "image", "src": self.a, "duration": 2}], audio={"voice": [{"src": "n.wav"}]})
        code, d = run(["--timeline", tl, "--output", self.out(), "--confirm"])
        self.assertEqual(code, 2); self.assertIn("narration is never cut", d["error"])

    def test_voice_meta_must_match_audio(self):
        tone_wav(os.path.join(self.dir, "n.wav"), 1.0)
        meta = self.voice_meta("n.wav", audio_sha256="0" * 64)
        tl = self.timeline([{"type": "image", "src": self.a, "duration": 2}],
                           audio={"voice": [{"src": "n.wav", "meta": meta}]})
        code, d = run(["--timeline", tl])
        self.assertEqual(code, 2); self.assertIn("does not match its yt-voice metadata", d["error"])
        meta = self.voice_meta("n.wav", duration=1.0)
        tl = self.timeline([{"type": "image", "src": self.a, "duration": 2}],
                           audio={"voice": [{"src": "n.wav", "meta": meta}]})
        code, d = run(["--timeline", tl])
        self.assertEqual((code, d["status"], d["plan"]["narration"]["voice_name"]), (2, "confirm_required", "Adam"))

    def test_bad_voice_inputs(self):
        with open(os.path.join(self.dir, "x.wav"), "w") as f: f.write("not audio")
        cases = [({"src": "missing.wav"}, "not found"), ({"src": self.a}, "unsupported audio type"),
                 ({"src": "x.wav"}, "ffprobe cannot read"),
                 ([{"src": "x.wav"}, {"src": "x.wav"}], "exactly one narration track")]
        for voice, msg in cases:
            tl = self.timeline([{"type": "image", "src": self.a, "duration": 2}], audio={"voice": voice})
            code, d = run(["--timeline", tl])
            self.assertEqual(code, 2, voice); self.assertIn(msg, d["error"])

    def test_subtitles_and_credit_burned_in(self):
        tone_wav(os.path.join(self.dir, "n.wav"), 2.5)
        with open(os.path.join(self.dir, "c.srt"), "w") as f: f.write(SRT)
        clip = {"type": "landsat", "src": self.a, "duration": 3, "motion": {"type": "static"},
                "credit": "Landsat imagery courtesy of the U.S. Geological Survey"}
        plain = self.timeline([clip], audio={"voice": [{"src": "n.wav"}]})
        run(["--timeline", plain, "--output", self.out("plain.mp4"), "--confirm"])
        tl = self.timeline([clip], audio={"voice": [{"src": "n.wav"}]},
                           subtitles={"src": "c.srt", "burn_in": True}, credit={})
        code, d = run(["--timeline", tl, "--output", self.out("subs.mp4"), "--confirm"])
        self.assertEqual((code, d["status"]), (0, "ok"), d)
        self.assertEqual((d["subtitles"]["cues"], d["credit"]),
                         (2, "Landsat imagery courtesy of the U.S. Geological Survey"))
        self.assertNotIn("warnings", d)
        # the picture differs from the same render without text, and only where text is drawn
        import subprocess as sp
        def frame(p, t):
            return sp.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", p, "-frames:v", "1", "-f", "rawvideo",
                           "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
        W, H = 320, 180
        a, b = frame(self.out("plain.mp4"), 1.0), frame(self.out("subs.mp4"), 1.0)
        diff_rows = [y for y in range(H) if any(abs(a[y * W + x] - b[y * W + x]) > 40 for x in range(W))]
        self.assertTrue(diff_rows, "no text drawn")
        self.assertTrue(any(y > H * 0.6 for y in diff_rows), "no subtitle in the lower part")
        self.assertTrue(any(y < H * 0.25 for y in diff_rows), "no credit in the top band")
        a, b = frame(self.out("plain.mp4"), 2.85), frame(self.out("subs.mp4"), 2.85)   # after the last cue
        self.assertFalse([y for y in range(int(H * 0.6), H) if any(abs(a[y * W + x] - b[y * W + x]) > 40
                                                                    for x in range(W))])
        self.assertEqual([f for f in os.listdir(self.dir) if f.startswith(".render")], [])

    def test_subtitle_validation(self):
        bad = {"overlap.srt": SRT.replace("00:00:01,400 --> 00:00:02,600", "00:00:01,000 --> 00:00:02,600"),
               "late.srt": SRT.replace("00:00:02,600", "00:00:09,000"),
               "junk.srt": "hello", "x.vtt": "WEBVTT"}
        for name, body in bad.items():
            with open(os.path.join(self.dir, name), "w") as f: f.write(body)
            tl = self.timeline([{"type": "image", "src": self.a, "duration": 3}], subtitles={"src": name})
            code, d = run(["--timeline", tl])
            self.assertEqual(code, 2, name)
        with open(os.path.join(self.dir, "ok.srt"), "w") as f: f.write(SRT)
        tl = self.timeline([{"type": "image", "src": self.a, "duration": 3}], subtitles={"src": "ok.srt", "burn_in": False})
        code, d = run(["--timeline", tl])
        self.assertEqual((d["status"], d["plan"]["subtitles"]["burn_in"]), ("confirm_required", False))
        for sub in ({"src": "ok.srt", "font": "x;rm"}, {"src": "ok.srt", "burn_in": "yes"}):
            tl = self.timeline([{"type": "image", "src": self.a, "duration": 3}], subtitles=sub)
            self.assertEqual(run(["--timeline", tl])[0], 2, sub)

    def test_credit_rules_and_landsat_warning(self):
        clip = {"type": "landsat", "src": self.a, "duration": 2}
        tl = self.timeline([clip])
        d = run(["--timeline", tl])[1]
        self.assertTrue(any("credit" in w for w in d["plan"]["warnings"]))
        self.assertEqual(run(["--timeline", self.timeline([clip], credit={})])[0], 2)   # no text anywhere
        d = run(["--timeline", self.timeline([clip], credit={"text": "USGS", "position": "bottom_right"})])[1]
        self.assertEqual(d["plan"]["credit"], "USGS")
        for bad in ({"text": "a\nb"}, {"text": "x", "position": "middle"}, {"text": "x", "size": 500}):
            self.assertEqual(run(["--timeline", self.timeline([clip], credit=bad)])[0], 2, bad)

    def test_version_2_accepted_same_render(self):
        clips = [{"type": "image", "src": self.a, "duration": 1}]
        h1 = run(["--timeline", self.timeline(clips), "--output", self.out("1.mp4"), "--confirm"])[1]["sha256"]
        p = self.timeline(clips)
        with open(p) as f: t = json.load(f)
        t["version"] = 2
        with open(p, "w") as f: json.dump(t, f)
        h2 = run(["--timeline", p, "--output", self.out("2.mp4"), "--confirm"])[1]["sha256"]
        self.assertEqual(h1, h2)
        t["version"] = 3
        with open(p, "w") as f: json.dump(t, f)
        self.assertEqual(run(["--timeline", p])[0], 2)


class BackwardCompat(Base):
    def test_plain_timeline_command_unchanged(self):
        """Without voice/subtitles/credit the ffmpeg command is the v1 command: silent track,
        no subtitle or drawtext filter, no extra inputs."""
        plan = {"output": dict(r.DEFAULT_OUTPUT), "total_frames": 30, "expected_duration": 1.0,
                "clips": [{"src": "/x/a.png", "frames": 30, "zoom": (1.0, 1.1), "pan": "center",
                           "fit": "cover", "transition_frames": 0}]}
        cmd = r.build_command(plan, "/x/out.mp4", 1 << 30)
        fc = cmd[cmd.index("-filter_complex") + 1]
        self.assertIn("anullsrc=r=48000:cl=stereo", cmd)
        self.assertNotIn("subtitles", fc); self.assertNotIn("drawtext", fc); self.assertNotIn("volume=", fc)
        self.assertEqual(cmd[cmd.index("-map") + 3], "1:a")
        self.assertTrue(fc.endswith("settb=1/30,setpts=N,format=yuv420p[vout]"))


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
