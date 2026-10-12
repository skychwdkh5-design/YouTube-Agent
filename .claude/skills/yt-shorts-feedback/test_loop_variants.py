#!/usr/bin/env python3
"""Offline tests for loopcheck.py and variants.py - synthetic fixtures, local ffmpeg only where noted.

    python3 test_loop_variants.py
"""
import io, json, os, shutil, subprocess, sys, tempfile, unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "yt-geo"))
import loopcheck as lc
import variants as vr

HAVE_FF = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))

def call(mod, argv):
    buf = io.StringIO()
    with redirect_stdout(buf): code = mod.main(argv)
    return code, json.loads(buf.getvalue())

class TextSeam(unittest.TestCase):
    def test_dangling_last_word_and_shared_words(self):
        cues = [[0.0, 1.5, "THE SAHARA"], [1.5, 3.0, "WAS GREEN"], [10.0, 11.5, "AND THE SAHARA IS"], [11.5, 13.0, "WITH THE"]]
        t = lc.text_seam(cues); names = [f["name"] for f in t["flags"]]
        self.assertIn("dangling_last_word", names); self.assertEqual(t["shared_content_words"], ["SAHARA"]); self.assertNotIn("no_shared_content_word", names)
        self.assertIn("|", t["seam_reads_as"])
    def test_no_shared_word_is_a_weak_flag_not_a_failure(self):
        t = lc.text_seam([[0, 2, "THIS IS EAST OWEINAT"], [40, 42, "SO WE CAN GREEN IT"]]); self.assertEqual([f["name"] for f in t["flags"]], ["no_shared_content_word"])
    def test_windows_collect_fragment_cues(self):
        t = lc.text_seam([[0, 1, "YOU COULD"], [1, 2, "TURN IT"], [20, 21, "A WEAK"], [21, 22, "INCREASE"]], window=2.0)
        self.assertEqual(t["first_window"]["text"], "YOU COULD TURN IT"); self.assertEqual(t["last_window"]["text"], "A WEAK INCREASE")
    def test_needs_two_cues(self):
        with self.assertRaises(lc.LoopError): lc.text_seam([[0, 1, "X"]])
    def test_srt_reader(self):
        d = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, d, True); p = os.path.join(d, "c.srt")
        with open(p, "w") as f: f.write("1\n00:00:00,100 --> 00:00:01,500\nHELLO THERE\n\n2\n00:00:09,000 --> 00:00:10,250\nGOODBYE\n")
        c = lc.read_srt(p); self.assertEqual((c[0][2], c[1][0], round(c[1][1], 2)), ("HELLO THERE", 9.0, 10.25))
    def test_the_published_shorts_have_no_designed_loop(self):
        with open(os.path.join(HERE, "..", "..", "..", "analytics", "shorts", "videos.json")) as f: vids = json.load(f)["videos"]
        for v in vids:
            s = v["structure_from_captions"]; self.assertEqual(s["seam_shared_content_words"], []); self.assertEqual(v["annotations"]["declared_loop_strategy"], "none")

@unittest.skipUnless(HAVE_FF, "ffmpeg not installed")
class VideoSeam(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp()
        def make(name, vf, audio):
            p = os.path.join(cls.dir, name)
            cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", vf] + (["-f", "lavfi", "-i", audio, "-shortest"] if audio else []) + ["-t", "2", "-pix_fmt", "yuv420p", "-r", "10", p]
            subprocess.run(cmd, check=True); return p
        cls.same = make("same.mp4", "color=c=0x2060c0:s=108x192:d=2", "sine=f=440:d=2")
        cls.diff = make("diff.mp4", "color=c=0x2060c0:s=108x192:d=1[a];color=c=0xe0a020:s=108x192:d=1[b];[a][b]concat=n=2:v=1:a=0", None) if False else None
        p = os.path.join(cls.dir, "diff.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x2060c0:s=108x192:d=1:r=10", "-f", "lavfi", "-i", "color=c=0xe0a020:s=108x192:d=1:r=10", "-filter_complex", "[0][1]concat=n=2:v=1:a=0", "-pix_fmt", "yuv420p", p], check=True); cls.diff = p
    @classmethod
    def tearDownClass(cls): shutil.rmtree(cls.dir, True)
    def test_identical_first_and_last_frame(self):
        v = lc.visual_seam(self.same); self.assertEqual(v["label"], "near_identical"); self.assertLess(v["first_vs_last_frame_mean_abs_diff"], 0.01)
    def test_different_first_and_last_frame(self):
        v = lc.visual_seam(self.diff); self.assertEqual(v["label"], "different"); self.assertGreater(v["first_vs_last_frame_mean_abs_diff"], 0.1)
    def test_audio_seam(self):
        a = lc.audio_seam(self.same); self.assertTrue(a["available"]); self.assertEqual(a["label"], "smooth"); self.assertFalse(lc.audio_seam(self.diff)["available"])
    def test_declared_visual_return_is_checked_against_the_picture(self):
        r = lc.report(None, self.diff, "visual_return"); self.assertEqual(r["verdict"], "needs_review"); self.assertTrue(r["review_notes"])
        r = lc.report(None, self.same, "visual_return"); self.assertEqual(r["verdict"], "seam_ok_by_measurement")
    def test_undeclared_near_identical_seam_asks_for_the_strategy_to_be_recorded(self):
        self.assertTrue(any("record the strategy" in n for n in lc.report(None, self.same, None)["review_notes"]))
    def test_cli(self):
        code, d = call(lc, ["--video", self.same, "--declared", "visual_return"]); self.assertEqual(code, 0); self.assertIn("visual", d)
        code, d = call(lc, ["--video", os.path.join(self.dir, "missing.mp4")]); self.assertEqual(code, 2)
    def test_bad_declaration(self):
        with self.assertRaises(lc.LoopError): lc.report(None, None, "nonsense")

CENTER = [-114.5, 36.2]
def _w(p, d):
    with open(p, "w") as f: json.dump(d, f)
def base_timeline():
    return {"version": 3, "profile": "short", "grid": "stack/grid.json",
            "assets": {"a": {"src": "stack/a.png", "label": "2000", "credit": "Test A"}, "b": {"src": "stack/b.png", "label": "2026", "credit": "Test B"}},
            "shots": [{"id": "hook", "start": 0, "claims": ["c1"], "camera": {"from": {"center": CENTER, "width_km": 12}, "to": {"center": CENTER, "width_km": 8}}, "layers": [{"type": "image", "asset": "a"}, {"type": "label", "text": "2000", "style": "year", "slot": "top"}]},
                      {"id": "proof", "start": 0.6, "claims": ["c2"], "camera": {"center": CENTER, "width_km": 6}, "layers": [{"type": "image", "asset": "b"}]}],
            "end": {"seconds": 1.4}}
SPEC = {"experiment_id": "EXP-T", "factor": "first_3s", "base_timeline": "timeline.json", "variable_shots": ["hook"],
        "variants": [{"id": "A", "name": "outcome_first", "set": {"hook": {"layers": [{"type": "image", "asset": "b"}, {"type": "label", "text": "GREEN NOW", "style": "year", "slot": "top"}]}}},
                     {"id": "B", "name": "orientation_first", "set": {"hook": {"layers": [{"type": "image", "asset": "a"}, {"type": "label", "text": "EAST OWEINAT", "style": "year", "slot": "top"}]}}}]}

class Variants(unittest.TestCase):
    def setUp(self): self.base = base_timeline()
    def test_only_declared_shots_and_keys_may_change(self):
        t = vr.apply_variant(self.base, SPEC["variants"][0], ["hook"]); self.assertEqual(t["shots"][0]["layers"][1]["text"], "GREEN NOW"); self.assertEqual(self.base["shots"][0]["layers"][1]["text"], "2000")
        for bad, msg in (({"proof": {"info": "x"}}, "not a declared variable shot"), ({"ghost": {"info": "x"}}, "not a declared"), ({"hook": {"claims": ["c9"]}}, "claims"), ({"hook": {"start": 1}}, "timing"),
                         ({"hook": {"spoken": "new line"}}, "TTS"), ({"hook": {"voice": {}}}, "approval"), ({"hook": {"zoom": 2}}, "unknown override")):
            with self.assertRaises(vr.VarError) as c: vr.apply_variant(self.base, {"id": "X", "set": bad}, ["hook"])
            self.assertIn(msg, str(c.exception))
    def test_single_variable_check_catches_leaks(self):
        a = vr.apply_variant(self.base, SPEC["variants"][0], ["hook"]); self.assertEqual(vr.check_single_variable(self.base, {"A": a}, ["hook"]), [])
        leak = json.loads(json.dumps(a)); leak["shots"][1]["camera"]["width_km"] = 5; self.assertTrue(any("other_shots" in x for x in vr.check_single_variable(self.base, {"A": leak}, ["hook"])))
        leak = json.loads(json.dumps(a)); leak["end"]["seconds"] = 2; self.assertTrue(any("everything_else" in x for x in vr.check_single_variable(self.base, {"A": leak}, ["hook"])))
        leak = json.loads(json.dumps(a)); leak["shots"][0]["start"] = 0.1; self.assertTrue(any("variable_shots_fixed_fields" in x for x in vr.check_single_variable(self.base, {"A": leak}, ["hook"])))
        leak = json.loads(json.dumps(a)); leak["assets"]["a"]["credit"] = "other"; self.assertTrue(any("redefined" in x for x in vr.check_single_variable(self.base, {"A": leak}, ["hook"])))
    def test_first_seconds_report(self):
        out = vr.first_seconds(self.base, 3.0); self.assertEqual([s["id"] for s in out], ["hook", "proof"]); self.assertEqual(out[0]["layers"][1]["text"], "2000")
        self.assertEqual([s["id"] for s in vr.first_seconds(self.base, 0.5)], ["hook"])
        tl = json.loads(json.dumps(self.base)); tl["shots"][1]["start"] = {"word": 1}
        self.assertIn("note", vr.first_seconds(tl, 3.0)[1]); self.assertEqual(vr.first_seconds(tl, 3.0, [{"start": 0, "end": 0.4}, {"start": 0.5, "end": 0.9}])[1]["start"], 0.5)
    def test_loop_close_returns_to_the_opening_view(self):
        t = vr.close_loop(self.base, 1.0); last = t["shots"][-1]
        self.assertEqual(last["id"], "loop_return"); self.assertEqual(last["camera"]["to"], self.base["shots"][0]["camera"]["from"]); self.assertEqual(last["camera"]["from"], self.base["shots"][-1]["camera"])
        self.assertEqual([L["type"] for L in last["layers"]], ["image", "label"]); self.assertNotIn("loop_return", [s["id"] for s in self.base["shots"]])
        with self.assertRaises(vr.VarError): vr.close_loop(t, 1.2)
        with self.assertRaises(vr.VarError): vr.close_loop(self.base, 0.4)
        with self.assertRaises(vr.VarError): vr.close_loop({"shots": [self.base["shots"][0]]}, 5)
    def test_loop_close_keeps_only_layers_visible_at_the_first_frame(self):
        tl = json.loads(json.dumps(self.base)); tl["shots"][0]["layers"].append({"type": "label", "text": "LATER", "t": [0.5, None]}); tl["shots"][0]["layers"].append({"type": "label", "text": "NOW", "t": [0, 1]})
        texts = [L.get("text") for L in vr.close_loop(tl, 1.0)["shots"][-1]["layers"]]; self.assertNotIn("LATER", texts); self.assertIn("NOW", texts)

class Integration(unittest.TestCase):
    """real validation through render.py WITHOUT --confirm: nothing is rendered"""
    @classmethod
    def setUpClass(cls):
        try:
            import numpy as np; from PIL import Image; import geostack as g
        except ImportError as e: raise unittest.SkipTest(f"needs numpy, Pillow and yt-geo: {e}")
        cls.dir = tempfile.mkdtemp(); os.makedirs(os.path.join(cls.dir, "stack"))
        x, y = g.lonlat_to_utm(CENTER[0], CENTER[1], 32611)
        with open(os.path.join(cls.dir, "stack", "grid.json"), "w") as f: json.dump({"schema": "yt-geo-stack/1", "epsg": 32611, "x0": float(x) - 15000, "y_top": float(y) + 15000, "pixel_m": 30.0, "width": 1000, "height": 1000}, f)
        for name, col in (("a", (40, 120, 200)), ("b", (200, 120, 40))):
            arr = np.zeros((1000, 1000, 3), np.uint8); arr[:] = col; arr[::50, :] = 255; Image.fromarray(arr).save(os.path.join(cls.dir, "stack", f"{name}.png"))
        with open(os.path.join(cls.dir, "timeline.json"), "w") as f: json.dump(base_timeline(), f)
        with open(os.path.join(cls.dir, "spec.json"), "w") as f: json.dump(SPEC, f)
    @classmethod
    def tearDownClass(cls): shutil.rmtree(cls.dir, True)
    def test_base_timeline_is_valid(self):
        p = vr.plan_of(os.path.join(self.dir, "timeline.json"), self.dir); self.assertTrue(p["valid"], p); self.assertIsNotNone(p["compositions"])
    def test_build_writes_valid_single_variable_timelines_and_renders_nothing(self):
        out = os.path.join(self.dir, "out"); code, d = call(vr, ["build", os.path.join(self.dir, "spec.json"), "--out-dir", out, "--validate", "--media-root", self.dir])
        self.assertEqual(code, 0, d); self.assertEqual(sorted(d["variants"]), ["A", "B"])
        for v in d["variants"].values(): self.assertTrue(v["plan"]["valid"], v["plan"]); self.assertTrue(os.path.exists(v["timeline"]))
        self.assertEqual(sorted(os.listdir(out)), ["timeline.A.json", "timeline.B.json"])        # no .mp4: nothing was rendered
    def test_build_refuses_identical_variants_and_a_spoken_change(self):
        spec = json.loads(json.dumps(SPEC)); spec["variants"][1] = dict(spec["variants"][0], id="B")
        p = os.path.join(self.dir, "same.json"); _w(p, spec); code, d = call(vr, ["build", p, "--out-dir", os.path.join(self.dir, "o2")]); self.assertEqual(code, 2); self.assertIn("identical", d["error"])
        spec = json.loads(json.dumps(SPEC)); spec["variants"][0]["set"]["hook"]["spoken"] = "another line"
        p = os.path.join(self.dir, "spoken.json"); _w(p, spec); code, d = call(vr, ["build", p, "--out-dir", os.path.join(self.dir, "o3")]); self.assertEqual(code, 2); self.assertIn("TTS", d["error"])
    def test_loop_close_timeline_validates(self):
        out = os.path.join(self.dir, "loop.json"); code, d = call(vr, ["loop-close", os.path.join(self.dir, "timeline.json"), "--start", "0.9", "--out", out, "--validate", "--media-root", self.dir])
        self.assertEqual(code, 0, d); self.assertTrue(d["plan"]["valid"], d["plan"]); self.assertEqual(d["declared_strategy"], "visual_return")
    def test_first_seconds_cli(self):
        code, d = call(vr, ["first-seconds", os.path.join(self.dir, "timeline.json")]); self.assertEqual((code, d["status"]), (0, "ok")); self.assertEqual(d["shots"][0]["id"], "hook")
    def test_errors_are_json(self):
        code, d = call(vr, ["build", os.path.join(self.dir, "nope.json")]); self.assertEqual(code, 2); self.assertEqual(d["status"], "error")

if __name__ == "__main__":
    unittest.main()
