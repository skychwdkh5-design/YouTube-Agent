#!/usr/bin/env python3
"""Offline tests for timeline version 3 (compose.py) - synthetic grid and imagery, local ffmpeg.

    python3 test_compose.py
"""
import io, json, os, shutil, subprocess, sys, tempfile, unittest, wave, struct
from contextlib import redirect_stdout

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render as r
import compose as c

HAVE_FF = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
sys.path.insert(0, os.path.join(HERE, "..", "yt-geo"))
import geostack as g

CENTER = [-114.5, 36.2]


def run(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = r.main(argv)
    return code, json.loads(buf.getvalue())


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        os.makedirs(os.path.join(self.dir, "stack"))
        x, y = g.lonlat_to_utm(CENTER[0], CENTER[1], 32611)
        self.grid = {"schema": "yt-geo-stack/1", "epsg": 32611, "x0": float(x) - 15000, "y_top": float(y) + 15000,
                     "pixel_m": 30.0, "width": 1000, "height": 1000}
        json.dump(self.grid, open(os.path.join(self.dir, "stack", "grid.json"), "w"))
        for name, col in (("a", (40, 120, 200)), ("b", (200, 120, 40))):
            arr = np.zeros((1000, 1000, 3), np.uint8); arr[:] = col
            arr[::50, :] = 255
            Image.fromarray(arr).save(os.path.join(self.dir, "stack", f"{name}.png"))
        m = np.zeros((1000, 1000), np.uint8); m[300:700, 300:700] = 255
        Image.fromarray(m).save(os.path.join(self.dir, "stack", "m.png"))

    def assets(self):
        return {"a": {"src": "stack/a.png", "label": "2000", "credit": "Test A"},
                "b": {"src": "stack/b.png", "label": "2026", "credit": "Test B"},
                "m": {"src": "stack/m.png", "kind": "mask"}}

    def timeline(self, shots, **extra):
        tl = {"version": 3, "profile": "short", "grid": "stack/grid.json", "assets": self.assets(),
              "shots": shots, "end": {"seconds": 1.2}}
        tl.update(extra)
        p = os.path.join(self.dir, "timeline.json")
        json.dump(tl, open(p, "w"))
        return p

    def shot(self, start=0, **kw):
        s = {"id": f"s{start}", "start": start, "camera": {"center": CENTER, "width_km": 12},
             "layers": [{"type": "image", "asset": "b"}]}
        s.update(kw)
        return s


class Validation(Base):
    def test_plan_and_events(self):
        tl = self.timeline([self.shot(0, info="hook", layers=[
                                {"type": "image", "asset": "b"},
                                {"type": "fill", "mask": "m", "color": "#FF7A28"},
                                {"type": "label", "text": "2026", "t": [0.2, None], "info": "year"}]),
                            self.shot(0.5, layers=[{"type": "flip", "assets": ["a", "b", "a"], "step": 0.2}])])
        code, d = run(["--timeline", tl])
        self.assertEqual((code, d["status"]), (2, "confirm_required"), d)
        p = d["plan"]
        self.assertEqual((p["version"], p["expected_duration"], p["total_frames"]), (3, 1.2, 36))
        self.assertEqual([e["what"] for e in p["info_events"]], ["hook", "year", "flip to b", "flip to a"])

    def test_camera_must_stay_on_the_imagery(self):
        tl = self.timeline([self.shot(0, camera={"center": CENTER, "width_km": 25})])   # 44 km tall > 30 km grid
        code, d = run(["--timeline", tl])
        self.assertEqual(code, 2); self.assertIn("leaves the imagery", d["error"])

    def test_rules(self):
        cases = [
            ([self.shot(0.3)], "first shot must start at 0"),
            ([self.shot(0), self.shot(0)], "starts at or before"),
            ([self.shot(0, layers=[{"type": "label", "text": "x"}])], "needs an image"),
            ([self.shot(0, layers=[{"type": "image", "asset": "m"}])], "not a image asset"),
            ([self.shot(0, layers=[{"type": "fill", "mask": "a"}, {"type": "image", "asset": "a"}])], "not a mask asset"),
            ([self.shot(0, layers=[{"type": "image", "asset": "a"}, {"type": "label", "text": "x" * 41}])], "1-40"),
            ([self.shot(0, layers=[{"type": "image", "asset": "a"}, {"type": "fill", "mask": "m", "color": "red"}])], "#RRGGBB"),
            ([self.shot(0, layers=[{"type": "sparkle"}])], "type must be one of"),
        ]
        for shots, msg in cases:
            code, d = run(["--timeline", self.timeline(shots)])
            self.assertEqual(code, 2, msg); self.assertIn(msg, d["error"])

    def test_assets_need_credit_and_matching_size(self):
        a = self.assets(); del a["a"]["credit"]
        code, d = run(["--timeline", self.timeline([self.shot(0)], assets=a)])
        self.assertIn("credit", d["error"])
        Image.new("RGB", (10, 10)).save(os.path.join(self.dir, "stack", "small.png"))
        a = self.assets(); a["a"]["src"] = "stack/small.png"
        code, d = run(["--timeline", self.timeline([self.shot(0)], assets=a)])
        self.assertIn("but the grid is", d["error"])

    def test_word_anchors_need_timings(self):
        tl = self.timeline([self.shot(0), self.shot({"word": 1})])
        code, d = run(["--timeline", tl])
        self.assertIn("no word timings", d["error"])

    def test_duration_limit(self):
        code, d = run(["--timeline", self.timeline([self.shot(0)], end={"seconds": 61})])
        self.assertEqual(code, 2)


@unittest.skipUnless(HAVE_FF, "ffmpeg not installed")
class Rendering(Base):
    def voice(self, seconds=1.0):
        path = os.path.join(self.dir, "n.wav")
        with wave.open(path, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(44100)
            w.writeframes(b"".join(struct.pack("<h", int(8000 * np.sin(i / 20))) for i in range(int(seconds * 44100))))
        meta = {"schema": "yt-voice/1", "audio_sha256": r._sha256(path), "duration": seconds,
                "voice_name": "Adam", "voice_id": "pNInz6obpgDQGcFmaJgB",
                "words": [{"text": "Hello", "start": 0.05, "end": 0.4}, {"text": "world.", "start": 0.5, "end": 0.9}]}
        json.dump(meta, open(os.path.join(self.dir, "n.voice.json"), "w"))
        with open(os.path.join(self.dir, "c.srt"), "w") as f:
            f.write("1\n00:00:00,050 --> 00:00:00,400\nHello\n\n2\n00:00:00,500 --> 00:00:00,900\nworld.\n")

    def test_full_short_render_with_voice_captions_and_manifest(self):
        self.voice()
        tl = self.timeline(
            [self.shot(0, info="hook", layers=[{"type": "image", "asset": "b"},
                                               {"type": "fill", "mask": "m", "color": "#FF0000", "opacity": 1.0}]),
             self.shot({"word": 1}, info="wipe", camera={"from": {"center": CENTER, "width_km": 12},
                                                         "to": {"center": [-114.49, 36.2], "width_km": 10}},
                       layers=[{"type": "wipe", "from": "a", "to": "b", "t": [0, 0.3]},
                               {"type": "arrow", "from": [-114.52, 36.22], "to": [-114.49, 36.19], "t": [0.2, None]},
                               {"type": "pin", "at": [-114.5, 36.2], "text": "HERE"},
                               {"type": "outline", "mask": "m"}])],
            voice={"src": "n.wav", "meta": "n.voice.json"}, captions={"src": "c.srt", "preset": "short"},
            end={"after_last_word": 0.3})
        out = os.path.join(self.dir, "short.mp4")
        code, d = run(["--timeline", tl, "--output", out, "--confirm"])
        self.assertEqual((code, d["status"]), (0, "ok"), d)
        p = r.ffprobe_json(out)
        v = [s for s in p["streams"] if s["codec_type"] == "video"][0]
        self.assertEqual((v["width"], v["height"], v["avg_frame_rate"], v["codec_name"]), (1080, 1920, "30/1", "h264"))
        self.assertTrue(any(s["codec_type"] == "audio" for s in p["streams"]))
        man = json.load(open(os.path.join(self.dir, "short.manifest.json")))
        self.assertEqual([s["start"] for s in man["shots"]], [0.0, 0.5])       # word 1 starts at 0.5 s
        self.assertEqual([s["credit"] for s in man["shots"]], ["Test B", "Test A / Test B"])
        self.assertEqual(len(man["caption_boxes"]), 2)
        for cb in man["caption_boxes"]:
            x0, y0, x1, y1 = cb["box"]
            self.assertTrue(1920 * 0.08 <= y0 and y1 <= 1920 * 0.78 and x1 <= 1080 * 0.88)
        # first frame already carries the t0 = 0 fill (the hook is visible from frame one)
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", out, "-frames:v", "1", "-f", "rawvideo",
                              "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        f0 = np.frombuffer(raw, np.uint8).reshape(1920, 1080, 3)
        self.assertGreater(int(f0[960, 540, 0]), 200)                      # red fill in the middle
        self.assertLess(int(f0[960, 540, 2]), 80)
        self.assertEqual([x for x in os.listdir(self.dir) if x.startswith(".render")], [])

    def test_failed_render_leaves_nothing(self):
        tl = self.timeline([self.shot(0)])
        real = c.subprocess.Popen

        def broken(cmd, **kw):            # only the encoder breaks; fc-match and ffprobe still work
            if cmd[0] == "ffmpeg" and "rawvideo" in cmd:
                cmd = ["ffmpeg", "-v", "error", "-f", "rawvideo", "-s", "4x4", "-i", "-", "-f", "nonexistent", "x"]
            return real(cmd, **kw)
        c.subprocess.Popen = broken
        try:
            code, d = run(["--timeline", tl, "--output", os.path.join(self.dir, "x.mp4"), "--confirm"])
        finally:
            c.subprocess.Popen = real
        self.assertEqual(code, 2)
        self.assertEqual(sorted(f for f in os.listdir(self.dir) if f.endswith(".mp4") or f.startswith(".render")), [])


class BackwardCompat(unittest.TestCase):
    def test_v1_and_v2_never_load_compose_path(self):
        self.assertEqual(r.SUPPORTED_VERSIONS, (1, 2))
        with self.assertRaises(r.RenderError):
            r.validate({"version": 3, "clips": []}, "/tmp")                # the v1 validator still refuses 3


if __name__ == "__main__":
    unittest.main(verbosity=1)
