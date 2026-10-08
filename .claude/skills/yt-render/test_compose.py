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
class Compositions(Base):
    """A composition reset is a new picture, not new text on the same picture."""
    def plan(self, shots, seconds):
        code, d = run(["--timeline", self.timeline(shots, end={"seconds": seconds})])
        self.assertEqual(d["status"], "confirm_required", d)
        return d["plan"]

    def test_overlays_and_year_swaps_are_not_resets(self):
        p = self.plan([self.shot(0, layers=[{"type": "image", "asset": "b"},
                                            {"type": "label", "text": "2026", "info": "year"}]),
                       self.shot(2, layers=[{"type": "image", "asset": "a"}, {"type": "outline", "mask": "m"},
                                            {"type": "label", "text": "-40%", "style": "stat", "info": "number"}]),
                       self.shot(4, camera={"from": {"center": CENTER, "width_km": 12},
                                            "to": {"center": CENTER, "width_km": 10}},       # slow push, 1.2x
                                 layers=[{"type": "flip", "assets": ["a", "b"], "step": 0.5},   # two dates: a swap
                                         {"type": "fill", "mask": "m"},
                                         {"type": "pin", "at": CENTER, "text": "HERE"}])], 8)
        c_ = p["compositions"]
        self.assertGreaterEqual(len(p["info_events"]), 3)                  # plenty of new information...
        self.assertEqual((c_["composition_resets"], c_["distinct_first_10s"]), (0, 1))   # ...one composition
        self.assertEqual(c_["longest_static_hold"]["seconds"], 8.0)
        w = " | ".join(p["warnings"])
        self.assertIn("only 1 distinct compositions in the first 10 s", w)
        self.assertIn("0 composition resets", w)
        self.assertIn("holds 8.0s", w)

    def test_zoom_relocation_wipe_timelapse_and_camera_move(self):
        moved = [CENTER[0] + 0.06, CENTER[1]]                              # about 5.4 km east
        p = self.plan([self.shot(0),
                       self.shot(1, layers=[{"type": "image", "asset": "a"}]),                # same view
                       self.shot(2, camera={"center": CENTER, "width_km": 6}),               # 2x zoom in
                       self.shot(3, camera={"center": moved, "width_km": 6}),                # relocation
                       self.shot(4, camera={"center": moved, "width_km": 6},
                                 layers=[{"type": "wipe", "from": "a", "to": "b", "t": [0.2, 0.8]}]),
                       self.shot(5, camera={"center": moved, "width_km": 6},
                                 layers=[{"type": "flip", "assets": ["a", "b", "a"], "step": 0.3}]),
                       self.shot(6, camera={"from": {"center": CENTER, "width_km": 6},
                                            "to": {"center": CENTER, "width_km": 14}, "ease": "linear"})], 9)
        rs = p["compositions"]["resets"]
        self.assertEqual([(x["shot"], x["kind"]) for x in rs],
                         [("s2", "cut"), ("s3", "cut"), ("s4", "wipe"), ("s5", "timelapse"), ("s6", "cut"),
                          ("s6", "camera_move")])
        self.assertEqual(rs[0]["what"], "zoom in x2.0")
        self.assertEqual(rs[1]["what"], "camera relocation")
        self.assertEqual(rs[2]["t"], 4.2)
        self.assertTrue(6.5 < rs[5]["t"] < 8.0, rs[5])                     # 6 -> 9 km reached mid-shot, 6 -> 14 km counted once
        self.assertEqual(p["compositions"]["distinct_first_10s"], 7)

    def test_simultaneous_changes_are_one_reset(self):
        p = self.plan([self.shot(0),
                       self.shot(1, camera={"center": CENTER, "width_km": 5},
                                 layers=[{"type": "wipe", "from": "a", "to": "b", "t": [0.15, 0.9]}])], 3)
        rs = p["compositions"]["resets"]
        self.assertEqual(len(rs), 1)
        self.assertEqual((rs[0]["kind"], rs[0]["also"]), ("cut", ["wipe"]))

    def test_continuous_transformation_is_not_a_static_hold(self):
        flip = {"type": "flip", "assets": ["a", "b", "a", "b", "a", "b", "a", "b", "a", "b"], "step": 0.7}
        p = self.plan([self.shot(0, layers=[flip])], 8)
        c_ = p["compositions"]
        self.assertEqual(c_["composition_resets"], 0)                      # a timelapse from frame one
        self.assertEqual(c_["segments"][0]["seconds"], 8.0)
        self.assertAlmostEqual(c_["longest_static_hold"]["seconds"], 1.0, places=3)   # 7 s of it is the timelapse
        self.assertFalse(any("holds" in w for w in p["warnings"]))


class VisualNovelty(Base):
    """A new composition of the same visual idea is not new: visual_family is a storyboard tag."""
    def plan(self, shots, seconds):
        code, d = run(["--timeline", self.timeline(shots, end={"seconds": seconds})])
        self.assertEqual(d["status"], "confirm_required", d)
        return d["plan"]

    def test_untagged_timelines_skip_the_rule(self):
        p = self.plan([self.shot(0), self.shot(2, camera={"center": CENTER, "width_km": 5})], 4)
        self.assertNotIn("visual_novelty", p)
        self.assertFalse(any("visual famil" in w for w in p["warnings"]))

    def test_new_compositions_of_one_family_are_not_novelty(self):
        moved = [CENTER[0] + 0.06, CENTER[1]]
        p = self.plan([self.shot(0, visual_family="green_circles"),
                       self.shot(4, camera={"center": CENTER, "width_km": 5}, visual_family="green_circles"),
                       self.shot(8, camera={"center": moved, "width_km": 6}, visual_family="green_circles")], 12)
        self.assertEqual(p["compositions"]["composition_resets"], 2)          # two new pictures...
        v = p["visual_novelty"]
        self.assertEqual((v["transitions"], v["families_first_10s"]), (0, 1))  # ...one visual idea
        self.assertEqual(v["longest_family_run"]["untransformed"], 12.0)
        w = " | ".join(p["warnings"])
        self.assertIn("only 1 visual families in the first 10 s", w)
        self.assertIn("0 visual-family transitions", w)
        self.assertIn("visual family 'green_circles' holds 12.0s", w)

    def test_layer_family_and_transformation(self):
        flip = {"type": "flip", "assets": ["a", "b", "a", "b", "a", "b", "a", "b", "a", "b", "a", "b"], "step": 1.0}
        p = self.plan([self.shot(0, visual_family="fields_now"),
                       self.shot(2, visual_family="fields_now",
                                 layers=[{"type": "wipe", "from": "b", "to": "a", "t": [1.0, 2.0],
                                          "visual_family": "empty_desert"}]),
                       self.shot(5, visual_family="growth_timelapse", layers=[flip]),
                       self.shot(17, visual_family="fields_now", camera={"center": CENTER, "width_km": 6})], 19)
        v = p["visual_novelty"]
        self.assertEqual([(r["family"], r["start"]) for r in v["runs"]],
                         [("fields_now", 0.0), ("empty_desert", 3.0), ("growth_timelapse", 5.0), ("fields_now", 17.0)])
        self.assertEqual((v["transitions"], v["families_first_10s"]), (3, 3))
        tl = v["runs"][2]
        self.assertEqual((tl["seconds"], tl["untransformed"]), (12.0, 0.0))  # 12 s, all of it transforming
        self.assertFalse(any("holds" in w and "visual family" in w for w in p["warnings"]))
        self.assertIn("3 visual-family transitions (target >= 6)", " | ".join(p["warnings"]))

    def test_tags_must_be_complete_and_well_formed(self):
        code, d = run(["--timeline", self.timeline([self.shot(0, visual_family="a"), self.shot(1)], end={"seconds": 2})])
        self.assertEqual(d["status"], "error"); self.assertIn("visual_family is set on some shots", d["error"])
        code, d = run(["--timeline", self.timeline([self.shot(0, visual_family="Lava Field!")], end={"seconds": 2})])
        self.assertEqual(d["status"], "error"); self.assertIn("snake_case", d["error"])
        code, d = run(["--timeline", self.timeline([self.shot(0, visual_family="x", layers=[
            {"type": "image", "asset": "b"}, {"type": "label", "text": "x", "visual_family": "y"}])], end={"seconds": 2})])
        self.assertEqual(d["status"], "error")                                # only image/flip/wipe carry a family


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
        self.assertEqual(man["compositions"]["rule"], "composition-reset/1")
        self.assertEqual([x["kind"] for x in man["compositions"]["resets"]], ["wipe"])   # 12 -> 10 km is no reset
        self.assertEqual(d["composition_resets"], 1)
        self.assertNotIn("visual_novelty", man)                               # untagged: block absent
        self.assertNotIn("visual_family", man["shots"][0])
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


@unittest.skipUnless(HAVE_FF, "ffmpeg/ffprobe not installed")
class LongProfile(Base):
    """profile "long": 1920x1080 documentary, segmented render, one narration mux."""
    voice = Rendering.voice
    def long_tl(self, seconds=3.2, segment_s=1, **extra):
        return self.timeline(
            [self.shot(0, info="hook", layers=[{"type": "image", "asset": "b"},
                                               {"type": "label", "text": "2026", "style": "year"},
                                               {"type": "pin", "at": CENTER, "text": "HERE"}]),
             self.shot(1.0, info="wipe", camera={"from": {"center": CENTER, "width_km": 12},
                                                 "to": {"center": [CENTER[0] + 0.03, CENTER[1]], "width_km": 8}},
                       layers=[{"type": "wipe", "from": "a", "to": "b", "t": [0, 0.6]},
                               {"type": "arrow", "from": [-114.52, 36.22], "to": [-114.49, 36.19]}]),
             self.shot(2.0, layers=[{"type": "flip", "assets": ["a", "b", "a"], "step": 0.3}])],
            profile="long", voice={"src": "n.wav", "meta": "n.voice.json"},
            captions={"src": "c.srt", "preset": "default"}, end={"seconds": seconds},
            **({"render": {"segment_s": segment_s}} if segment_s else {}), **extra)

    def probe(self, path):
        p = r.ffprobe_json(path)
        v = [s for s in p["streams"] if s["codec_type"] == "video"][0]
        a = [s for s in p["streams"] if s["codec_type"] == "audio"][0]
        return v, a

    def md5(self, path, stream):
        return subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-map", f"0:{stream}", "-f", "md5", "-"],
                              capture_output=True, text=True, check=True).stdout.strip()

    def frames(self, path, idx):
        out = []
        for i in idx:
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"select=eq(n\\,{i})", "-vsync", "0",
                                  "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                 capture_output=True, check=True).stdout
            out.append(np.frombuffer(raw, np.uint8).astype(np.float64))
        return out

    def test_plan_layout_and_rules(self):
        self.voice(3.0)
        code, d = run(["--timeline", self.long_tl()])
        self.assertEqual(d["status"], "confirm_required", d)
        p = d["plan"]
        self.assertEqual((p["profile"], p["total_frames"], p["segments"], p["segment_frames"]), ("long", 96, 4, 30))
        self.assertEqual(c.LAYOUTS["short"]["caption"], c.CAPTION)                 # Shorts layout untouched
        self.assertIn("resets_per_min", p["compositions"]["thresholds"])
        self.assertIn("duration 3.2s outside 60.0-900.0 s", p["warnings"])
        # captions preset per profile; render settings only for long; 15-minute cap
        tl = json.load(open(self.long_tl())); tl["captions"]["preset"] = "short"; json.dump(tl, open(os.path.join(self.dir, "x.json"), "w"))
        self.assertIn("captions.preset must be 'default'", run(["--timeline", os.path.join(self.dir, "x.json")])[1]["error"])
        tl = json.load(open(self.long_tl())); tl["end"] = {"seconds": 901}; json.dump(tl, open(os.path.join(self.dir, "x.json"), "w"))
        self.assertIn("901", run(["--timeline", os.path.join(self.dir, "x.json")])[1]["error"])
        short = self.timeline([self.shot(0)], render={"segment_s": 5}, end={"seconds": 1})
        self.assertIn("only for profile 'long'", run(["--timeline", short])[1]["error"])

    def test_long_rates_not_short_counts(self):
        self.voice(3.0)
        tl = json.load(open(self.long_tl())); tl["end"] = {"seconds": 120}; tl.pop("captions"); tl.pop("voice")
        json.dump(tl, open(os.path.join(self.dir, "x.json"), "w"))
        p = run(["--timeline", os.path.join(self.dir, "x.json")])[1]["plan"]
        w = " | ".join(p["warnings"])
        self.assertIn("/min (target >= 5/min)", w)                                 # a rate, not "about 7-10"
        self.assertNotIn("target about 7-10", w)
        self.assertIn("target <= 8s", w)                                           # long hold limit

    def test_segmented_render_sync_boundaries_and_determinism(self):
        self.voice(3.0)
        seg_out, one_out, again = (os.path.join(self.dir, n) for n in ("seg.mp4", "one.mp4", "again.mp4"))
        code, d = run(["--timeline", self.long_tl(segment_s=1), "--output", seg_out, "--confirm"])
        self.assertEqual((code, d["status"], d["segments"]), (0, "ok", 4), d)
        v, a = self.probe(seg_out)
        self.assertEqual((v["width"], v["height"], v["avg_frame_rate"], int(v["nb_frames"])), (1920, 1080, "30/1", 96))
        self.assertAlmostEqual(float(a["duration"]), 3.2, places=2)
        man = json.load(open(seg_out[:-4] + ".manifest.json"))
        self.assertEqual([(s["start_frame"], s["frames"]) for s in man["segments"]], [(0, 30), (30, 30), (60, 30), (90, 6)])
        H, W, safe = 1080, 1920, man["safe"]
        for cb in man["caption_boxes"]:
            x0, y0, x1, y1 = cb["box"]
            self.assertTrue(y0 >= H * safe["top"] and y1 <= H * (1 - safe["bottom"]) and x0 >= W * safe["left"]
                            and x1 <= W * (1 - safe["right"]), cb)
        self.assertEqual([s["credit"] for s in man["shots"]], ["Test B", "Test A / Test B", "Test A"])
        # deterministic: same timeline, same bytes
        run(["--timeline", self.long_tl(segment_s=1), "--output", again, "--confirm"])
        self.assertEqual(r._sha256(seg_out), r._sha256(again))
        # one segment vs four: identical narration, the same pictures at every boundary
        code, d = run(["--timeline", self.long_tl(segment_s=300), "--output", one_out, "--confirm"])
        self.assertEqual((code, d["segments"]), (0, 1), d)
        self.assertEqual(self.md5(seg_out, "a"), self.md5(one_out, "a"))
        idx = [0, 29, 30, 31, 59, 60, 89, 90, 95]
        for i, fa, fb in zip(idx, self.frames(seg_out, idx), self.frames(one_out, idx)):
            mse = float(np.mean((fa - fb) ** 2))
            psnr = 99.0 if mse == 0 else 10 * np.log10(255 ** 2 / mse)
            self.assertGreater(psnr, 38, f"frame {i}: {psnr:.1f} dB")
        # QC long: technically sound apart from the (intentional) 3 s duration; boundaries are keyframes
        sys.path.insert(0, os.path.join(HERE, "..", "yt-qc"))
        import qc
        rep = qc.run_qc(seg_out, profile="long", manifest=man)
        ids = {x["id"]: x["status"] for x in rep["checks"]}
        for k in ("resolution", "frame_rate", "frame_count", "streams_aligned", "full_decode", "captions_in_safe_zone",
                  "shot_credits", "segments_tile_video", "segment_boundaries_keyframes"):
            self.assertEqual(ids[k], "pass", k)
        self.assertEqual(ids["long_duration"], "fail")
        self.assertEqual([x for x in os.listdir(self.dir) if x.startswith(".render")], [])


@unittest.skipUnless(HAVE_FF, "ffmpeg/ffprobe not installed")
class Graphics(Base):
    """yt-graphics images as full-frame shots and timed inserts in a LONG timeline."""
    def make_graphics(self):
        sys.path.insert(0, os.path.join(HERE, "..", "yt-graphics"))
        import graphics as gx
        os.makedirs(os.path.join(self.dir, "graphics"), exist_ok=True)
        spec = {"graphics": [
            {"type": "diagram", "id": "d", "source": "TEST DATA", "title": "Diagram (TEST DATA)",
             "nodes": [{"id": "a", "text": "A", "x": 0.2, "y": 0.5}, {"id": "b", "text": "B", "x": 0.8, "y": 0.5, "step": 2}],
             "arrows": [{"from": "a", "to": "b", "step": 2}]},
            {"type": "callout", "id": "n", "source": "TEST DATA", "value": 42, "unit": "km", "label": "Callout (TEST DATA)"}]}
        gx.render_spec(spec, self.dir, os.path.join(self.dir, "graphics"))

    def gtl(self, shots, profile="long", **extra):
        a = self.assets()
        a.update({"d1": {"src": "graphics/d.step1.png", "kind": "graphic", "credit": "Graphic (TEST)", "group": "d"},
                  "d2": {"src": "graphics/d.png", "kind": "graphic", "credit": "Graphic (TEST)", "group": "d"},
                  "num": {"src": "graphics/n.png", "kind": "graphic", "credit": "Callout (TEST)"}})
        tl = {"version": 3, "profile": profile, "grid": "stack/grid.json", "assets": a, "shots": shots,
              "end": {"seconds": 4.0}}
        tl.update(extra)
        p = os.path.join(self.dir, "timeline.json")
        json.dump(tl, open(p, "w"))
        return p

    def shots(self):
        return [self.shot(0, camera={"center": CENTER, "width_km": 12}),
                {"id": "g", "start": 1.0, "layers": [{"type": "graphic", "asset": "d1"},
                                                    {"type": "graphic", "asset": "d2", "t": [1.0, None]}]},
                self.shot(3.0, camera={"center": CENTER, "width_km": 12},
                          layers=[{"type": "image", "asset": "b"}, {"type": "graphic", "asset": "num", "t": [0.3, 0.8]}])]

    def test_plan_rules(self):
        self.make_graphics()
        p = run(["--timeline", self.gtl(self.shots(), render={"segment_s": 1})])[1]["plan"]
        resets = [(x["t"], x["kind"]) for x in p["compositions"]["resets"]]
        # the graphic is a new picture; its build step (same group) is not; back to the map is
        self.assertEqual([k for _, k in resets][:2], ["graphic", "cut"])
        kinds = [x["kind"] for x in p["compositions"]["resets"]]
        self.assertIn("graphic", kinds)
        self.assertFalse(any(abs(x["t"] - 2.0) < 1e-6 for x in p["compositions"]["resets"]))
        bad = [({"id": "g", "start": 1.0, "layers": [{"type": "graphic", "asset": "d1", "t": [0.5, None]}]},
                "camera is required"),
               ({"id": "g", "start": 1.0, "layers": [{"type": "graphic", "asset": "d1"},
                                                    {"type": "pin", "at": CENTER, "text": "x"}]}, "cannot use map layers"),
               ({"id": "g", "start": 1.0, "layers": [{"type": "graphic", "asset": "a"}]}, "is not a graphic asset")]
        for shot, msg in bad:
            sh = self.shots(); sh[1] = shot
            self.assertIn(msg, run(["--timeline", self.gtl(sh)])[1]["error"])
        tl = json.load(open(self.gtl(self.shots()))); tl["assets"]["num"].pop("credit")
        json.dump(tl, open(os.path.join(self.dir, "x.json"), "w"))
        self.assertIn("needs an on-screen 'credit'", run(["--timeline", os.path.join(self.dir, "x.json")])[1]["error"])
        # a 1920x1080 graphic in a vertical Short is refused (wrong size for the profile)
        self.assertIn("profile short renders 1080x1920",
                      run(["--timeline", self.gtl(self.shots(), profile="short")])[1]["error"])

    def test_long_render_shows_the_graphics(self):
        self.make_graphics()
        out = os.path.join(self.dir, "g.mp4")
        code, d = run(["--timeline", self.gtl(self.shots(), render={"segment_s": 1}), "--output", out, "--confirm"])
        self.assertEqual((code, d["status"], d["segments"]), (0, "ok", 4), d)

        def frame(t):
            raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", out, "-frames:v", "1", "-f", "rawvideo",
                                  "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
            return np.frombuffer(raw, np.uint8).reshape(1080, 1920, 3).astype(float)

        def psnr(f, png):
            gimg = np.asarray(Image.open(os.path.join(self.dir, "graphics", png)).convert("RGB")).astype(float)
            m = np.ones((1080, 1920), bool); m[60:130, 60:900] = False      # the renderer's credit line
            mse = np.mean((f[m] - gimg[m]) ** 2)
            return 99.0 if mse == 0 else 10 * np.log10(255 ** 2 / mse)

        self.assertGreater(psnr(frame(1.5), "d.step1.png"), 35)
        self.assertGreater(psnr(frame(2.5), "d.png"), 35)                     # the build step appears on time
        self.assertGreater(psnr(frame(3.72), "n.png"), 35)                    # the timed insert, after its 0.35 s fade-in
        self.assertLess(psnr(frame(3.95), "n.png"), 25)                       # ... and it is gone again
        man = json.load(open(out[:-4] + ".manifest.json"))
        self.assertEqual([s["credit"] for s in man["shots"]], ["Test B", "Graphic (TEST)", "Test B"])
        self.assertEqual(man["shots"][1]["layers"], ["graphic", "graphic"])


class BackwardCompat(unittest.TestCase):
    def test_v1_and_v2_never_load_compose_path(self):
        self.assertEqual(r.SUPPORTED_VERSIONS, (1, 2))
        with self.assertRaises(r.RenderError):
            r.validate({"version": 3, "clips": []}, "/tmp")                # the v1 validator still refuses 3


if __name__ == "__main__":
    unittest.main(verbosity=1)
