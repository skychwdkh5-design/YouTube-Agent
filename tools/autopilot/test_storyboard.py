#!/usr/bin/env python3
"""Offline tests for the storyboard generator: synthetic images, local renderer plan, no network, no paid request."""
import json, os, shutil, sys, tempfile, unittest

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "memory"))
import effects, storyboard as sb  # noqa: E402

HAVE_FF = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
PROV = {"source_url": "https://example.org/t", "license": "TEST DATA", "retrieved": "2026-10-14"}
SCRIPT = """This is Lake Mead, the largest reservoir in the United States. In 2000 it was nearly full. Then the water began to fall.
Since 2000 the lake has dropped about 150 feet. That is the height of a fifteen story building.
Far away, the Aral Sea tells a harder story. Once one of the four largest lakes on Earth, it lost most of its water in fifty years. The shore moved dozens of miles. Ships were left stranded on sand.
[VIS: steps="Rivers diverted|Less water arrives|Sea shrinks|Shoreline retreats" label="HOW A LAKE VANISHES"]
It happened in four steps. Rivers were diverted to farms. Less water reached the sea. The sea shrank. The shoreline retreated.
At the mouth of the Colorado River, the delta is dry for most of the year. Water that once reached the sea is now used upstream. The river no longer finishes its journey.
"""
CLAIM = {"id": "C1", "text": "Lake Mead has dropped about 150 feet since 2000", "status": "VERIFIED", "source_url": "https://example.org/c1",
         "source_name": "TEST SOURCE", "evidence_type": "observation"}


def make_image(path, seed, size=(1800, 1013)):
    rng = np.random.default_rng(seed)
    w, h = size
    x = np.linspace(0, 1, w)[None, :, None]; y = np.linspace(0, 1, h)[:, None, None]
    a = (np.sin(x * 8 + seed) + np.cos(y * 6 - seed)) * 40 + 128
    arr = np.concatenate([a * (0.4 + 0.6 * x), a * (0.8 - 0.3 * y), a * (0.5 + 0.4 * np.sin(seed + x * 3))], axis=2)
    Image.fromarray(np.clip(arr + rng.normal(0, 5, arr.shape), 0, 255).astype("uint8")).save(path, quality=88)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.prod = os.path.join(self.tmp.name, "ep996-test")
        for d in ("assets", "story", "voice"):
            os.makedirs(os.path.join(self.prod, d))
        specs = [("mead", ["lake mead", "reservoir"], "Lake Mead"), ("mead2", ["lake mead", "reservoir"], "Lake Mead"),
                 ("aral", ["aral sea"], "Aral Sea"), ("delta", ["colorado river delta"], "Colorado River Delta")]
        self.manifest = []
        for i, (n, tags, place) in enumerate(specs, 1):
            make_image(os.path.join(self.prod, "assets", n + ".jpg"), i)
            self.manifest.append(dict(id=n, kind="still", src=f"assets/{n}.jpg", credit="TEST IMAGE · synthetic", tags=tags, place=place, **PROV))
        self.write_manifest()
        self.write("script.md", SCRIPT)
        self.write("story/claims.json", json.dumps({"claims": [CLAIM]}))

    def write(self, rel, text):
        with open(os.path.join(self.prod, rel), "w", encoding="utf-8") as f: f.write(text)

    def write_manifest(self):
        self.write("assets/manifest.json", json.dumps({"assets": self.manifest}))

    def plan(self, **kw):
        r = sb.plan_cmd(self.prod, **kw)
        self.tl = json.load(open(os.path.join(self.prod, "timeline.json")))
        self.pl = json.load(open(os.path.join(self.prod, "story", "storyboard.plan.json")))
        return r


class Generation(Base):
    def test_timeline_is_valid_for_the_real_renderer_and_estimated_timing_is_flagged(self):
        r = self.plan()
        self.assertTrue(r["ok"], r)
        self.assertEqual((self.tl["version"], self.tl["profile"]), (3, "long"))
        self.assertEqual(self.tl["meta"]["timing"], "estimated")
        self.assertIn("ESTIMATED", self.tl["meta"]["timing_note"])
        self.assertTrue(os.path.exists(os.path.join(self.prod, "story", "storyboard.md")))      # satisfies the pipeline's timeline gate

    def test_only_built_effects_are_ever_used(self):
        self.plan()
        built = {e["id"] for e in effects.load()["entries"] if e["status"] == "built" and e["renderer"].startswith("yt-render-v3")}
        for d in self.pl["scenes"]:
            self.assertIn(d["chosen"]["template"], built, d["chosen"])

    def test_no_unrelated_picture_is_ever_shown(self):
        r = self.plan()
        by = {a["id"]: a for a in self.manifest}
        subject = None
        for d in self.pl["scenes"]:
            asset = d["chosen"]["asset"]
            if asset is None: continue
            rel = sb.relevance({"text": d["text"], "hints": {}}, dict(by[asset], tags=[x.lower() for x in by[asset]["tags"]])) > 0
            cont = any("continuation" in n for n in d["notes"])
            self.assertTrue(rel or cont, (d["scene"], asset, d["text"][:60]))

    def test_scene_without_any_matching_asset_is_a_gap_not_a_fake(self):
        self.manifest = [a for a in self.manifest if a["id"] == "aral"]
        self.write_manifest()
        r = self.plan()
        self.assertTrue(r["gaps"], "scenes about Lake Mead have no picture and must be reported")
        shown = {L["asset"] for s in self.tl["shots"] for L in s["layers"] if L["type"] == "still"}
        self.assertEqual(shown, {"aral"})

    def test_hook_has_three_compositions_in_ten_seconds_when_pictures_exist(self):
        r = self.plan()
        self.assertGreaterEqual(r["compositions"]["distinct_first_10s"], 3, r["renderer_warnings"])

    def test_long_single_picture_runs_become_an_acquisition_list(self):
        r = self.plan()
        self.assertTrue(self.pl["needs"])
        n = self.pl["needs"][0]
        self.assertIn("second picture", n["need"])
        self.assertGreater(n["seconds"], sb.HOLD_S)

    def test_graphics_need_a_verified_claim_and_show_its_source(self):
        self.plan()
        self.assertTrue(any(a["kind"] == "graphic" and a["src"].endswith("callout_1.png") or "callout" in a["src"] for a in self.tl["assets"].values()))
        self.write("story/claims.json", json.dumps({"claims": [dict(CLAIM, status="PENDING")]}))
        self.plan()
        self.assertFalse(any("callout" in a["src"] for a in self.tl["assets"].values()), "an unverified claim must not become a number graphic")

    def test_flow_graphic_steps_come_from_the_script_and_are_word_anchored(self):
        self.plan()
        flow = [s for s in self.tl["shots"] if any(L["type"] == "graphic" and "flow" in L["asset"] for L in s["layers"])]
        self.assertTrue(flow)
        layers = flow[0]["layers"]
        self.assertGreaterEqual(len(layers), 4)
        times = [L["t"][0] for L in layers[1:]]
        self.assertEqual(times, sorted(times))
        self.assertTrue(all(t > 0 for t in times))

    def test_missing_provenance_is_refused(self):
        del self.manifest[0]["license"]
        self.write_manifest()
        with self.assertRaises(ValueError):
            sb.plan_cmd(self.prod)

    def test_provider_timings_are_used_when_present(self):
        blocks = sb.parse_script(SCRIPT)
        words = sb.estimate_words(blocks)
        for w in words: w["start"] = round(w["start"] * 1.1, 3); w["end"] = round(w["end"] * 1.1, 3)
        self.write("voice/narration.voice.json", json.dumps({"schema": "yt-voice/1", "words": words, "timing": {"source": "provider", "level": "word"}}))
        r = self.plan()
        self.assertEqual(self.tl["meta"]["timing"], "provider")
        self.assertNotIn("ESTIMATED", self.tl["meta"]["timing_note"])

    def test_alignment_survives_small_script_edits(self):
        blocks = sb.parse_script(SCRIPT)
        words = sb.estimate_words(blocks)
        edited = [dict(b) for b in blocks]
        edited[0] = dict(edited[0], text=edited[0]["text"].replace("largest ", ""))
        info = sb.align(edited, words)
        self.assertFalse(info["exact"])
        self.assertGreater(info["matched"], 0.9 * info["of"])

    def test_deterministic_output(self):
        self.plan(); a = open(os.path.join(self.prod, "timeline.json"), "rb").read()
        self.plan(); b = open(os.path.join(self.prod, "timeline.json"), "rb").read()
        self.assertEqual(a, b)


class Repair(unittest.TestCase):
    def test_known_renderer_errors_are_repaired(self):
        tl = {"shots": [{"id": "a", "start": 0, "layers": [{"type": "still", "asset": "x", "view": {"from": {"center": [0.1, 0.1], "width": 0.1}, "to": {"center": [0.1, 0.1], "width": 0.1}}}]},
                        {"id": "b", "start": 2, "layers": [{"type": "label", "text": "X" * 40}]}]}
        self.assertIn("widened", sb.repair(tl, "shot a: the from view of 'x' would magnify 9.00x (limit 4.0x)"))
        self.assertGreater(tl["shots"][0]["layers"][0]["view"]["from"]["width"], 0.1)
        self.assertIn("shortened", sb.repair(tl, "shots[1].layers[0].text must be 1-40 characters"))
        self.assertLessEqual(len(tl["shots"][1]["layers"][0]["text"]), sb.LABEL_MAX)
        self.assertIsNone(sb.repair(tl, "something nobody has seen before"))

    def test_views_never_leave_the_image_or_exceed_the_upscale_limit(self):
        a = {"size": [1800, 1013]}
        for cx, cy, w in ((0.0, 0.0, 0.3), (1.0, 1.0, 0.2), (0.5, 0.5, 1.5), (0.05, 0.95, 0.02)):
            v = sb.fit_view(a, cx, cy, w)
            bw = v["width"] * 1800; bh = bw * 9 / 16
            self.assertLessEqual(bh, 1013 + 1e-6)
            self.assertLessEqual(1920 / bw, sb.STILL_MAX_UPSCALE + 1e-6)
            self.assertGreaterEqual(v["center"][0] * 1800 - bw / 2, -1e-6)
            self.assertLessEqual(v["center"][1] * 1013 + bh / 2, 1013 + 1e-6)


@unittest.skipUnless(HAVE_FF, "ffmpeg not installed")
class Preview(Base):
    def test_preview_renders_a_real_silent_proof(self):
        self.plan()
        r = sb.preview_cmd(self.prod, 0, 6, confirm=True)
        self.assertEqual(r.get("status"), "ok", r)
        self.assertAlmostEqual(r["duration"], 6.0, delta=0.1)
        self.assertTrue(os.path.getsize(os.path.join(self.prod, "preview", "proof.mp4")) > 10000)
        t = json.load(open(os.path.join(self.prod, "timeline_preview.json")))
        self.assertNotIn("voice", t)
        self.assertIn("silent proof", t["meta"]["note"])


if __name__ == "__main__":
    unittest.main()
