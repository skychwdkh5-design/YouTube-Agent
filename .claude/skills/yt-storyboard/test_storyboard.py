#!/usr/bin/env python3
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import storyboard as sb

GRID = {"epsg": 32636, "x0": 706200.0, "y_top": 3116000.0, "pixel_m": 10.0, "width": 2180, "height": 928}


class Script(unittest.TestCase):
    def test_tags_directions_headings_not_spoken(self):
        ch, order = sb.parse_script("# T\n## a: One\nHello 170 km. {C1}\n[ON SCREEN: x]\nNot sure. {L}\n## b: Two\n**Bold** word.\n")
        self.assertEqual(order, ["a", "b"])
        self.assertEqual(ch["a"], ["Hello", "170", "km.", "Not", "sure."])
        self.assertEqual(ch["b"], ["Bold", "word."])

    def test_estimated_times_are_contiguous(self):
        t, how = sb.chapter_times({"a": ["w"] * 49, "b": ["w"] * 98}, ["a", "b"])
        self.assertEqual(how, "estimate")
        self.assertAlmostEqual(t["a"][1], t["b"][0])
        self.assertAlmostEqual(t["b"][1], 3 * 49 / sb.PACE_WPS)

    def test_voice_timings_must_match_word_count(self):
        meta = {"words": [{"text": "w", "start": i, "end": i + .5} for i in range(5)]}
        with self.assertRaises(sb.StoryError):
            sb.chapter_times({"a": ["w"] * 6}, ["a"], meta)
        t, how = sb.chapter_times({"a": ["w"] * 3, "b": ["w"] * 2}, ["a", "b"], meta)
        self.assertEqual(how, "voice")
        self.assertEqual(t["a"][0], 0.0)
        self.assertEqual(t["b"][0], t["a"][1])


class Camera(unittest.TestCase):
    def test_view_is_clamped_inside_stack(self):
        c, w = sb.fit_view(GRID, [35.10, 28.07], 15)          # corner of the stack
        self.assertLessEqual(w, 15)
        c2, w2 = sb.fit_view(GRID, [35.215, 28.11], 40)       # too wide: reduced to what fits
        self.assertLess(w2, 22)

    def test_split_respects_limits(self):
        parts = sb.split_duration(20)
        self.assertTrue(all(sb.MIN_SHOT_S <= p <= sb.MAX_SHOT_S for p in parts))
        self.assertAlmostEqual(sum(parts), 20)
        self.assertEqual(sb.split_duration(4), [4])


class Build(unittest.TestCase):
    def setUp(self):
        import tempfile, json
        self.d = tempfile.mkdtemp()
        json.dump(GRID, open(os.path.join(self.d, "grid.json"), "w"))
        self.ep = {"grid": "grid.json", "focus": [35.215, 28.11], "assets": {"a": {"src": "a.png"}, "g": {"src": "g.png", "kind": "graphic", "claims": ["C1"]}},
                   "chapters": [{"id": "one", "visuals": [{"asset": "g", "kind": "graphic", "min_s": 4}, {"asset": "a", "zoom": [12, 6], "label": {"text": "9 km", "claim": "C1"}}]}]}

    def write(self, text):
        open(os.path.join(self.d, "script.md"), "w").write(text)

    def test_shots_labels_and_graphic_claims(self):
        self.write("## one: One\n" + "word " * 60 + "\n")
        plan, labels = sb.build(self.ep, self.d)
        self.assertEqual(plan["shots"][0]["layers"][0]["type"], "graphic")
        self.assertAlmostEqual(plan["shots"][-1]["end"], 60 / sb.PACE_WPS, places=2)
        self.assertEqual({l["text"] for l in labels}, {"graphic:g", "9 km"})
        self.assertEqual([l for l in labels if l["text"] == "graphic:g"][0]["claims"], ["C1"])
        self.assertTrue(all(s["dur"] <= sb.MAX_SHOT_S + 0.01 for s in plan["shots"] if "camera" in s))

    def test_shot_ids_are_unique(self):
        self.ep["chapters"][0]["visuals"] = [{"asset": "a", "zoom": [12, 6]}, {"asset": "a", "zoom": [8, 4]}, {"asset": "a", "zoom": [10, 5]}]
        self.write("## one: One\n" + "word " * 80 + "\n")
        plan, _ = sb.build(self.ep, self.d)
        ids = [s["id"] for s in plan["shots"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_heading_mismatch_is_an_error(self):
        self.write("## other: X\nword word word\n")
        with self.assertRaises(sb.StoryError):
            sb.build(self.ep, self.d)

    def test_graphic_cannot_be_stretched_to_fill_time(self):
        self.ep["chapters"][0]["visuals"] = [{"asset": "g", "kind": "graphic", "min_s": 4}]
        self.write("## one: One\n" + "word " * 100 + "\n")
        with self.assertRaises(sb.StoryError):
            sb.build(self.ep, self.d)

    def test_timeline_strips_claims_keys(self):
        self.write("## one: One\n" + "word " * 60 + "\n")
        plan, _ = sb.build(self.ep, self.d)
        tl = sb.to_timeline(self.ep, plan, self.d)
        self.assertNotIn("claims", tl["assets"]["g"])
        self.assertEqual(tl["version"], 3)
        self.assertIn("seconds", tl["end"])


class Anchors(unittest.TestCase):
    """A year image / wipe reveal must be on screen when the narrator SAYS the year (the 9-15 s mismatch of the EP005 test render)."""
    def setUp(self):
        import tempfile, json
        self.d = tempfile.mkdtemp()
        json.dump(GRID, open(os.path.join(self.d, "grid.json"), "w"))
        self.assets = {f"y{y}": {"src": f"y{y}.png"} for y in (2020, 2022, 2026)}
        # 40 words; "2022" is word 20 and "2026" is word 28; voice paces 2 words per second
        text = "## one: One\n" + " ".join(["w"] * 20) + " 2022 " + " ".join(["w"] * 7) + " 2026 " + " ".join(["w"] * 10) + "\n"
        open(os.path.join(self.d, "script.md"), "w").write(text)
        self.words = [{"text": "w", "start": i / 2, "end": i / 2 + .4} for i in range(40)]
        self.vm = {"words": self.words}

    def ep(self, vis):
        return {"grid": "grid.json", "focus": [35.215, 28.11], "assets": self.assets, "chapters": [{"id": "one", "visuals": vis}]}

    def test_year_image_and_wipe_follow_the_spoken_year(self):
        vis = [{"asset": "y2020", "zoom": [20, 12]}, {"asset": "y2022", "zoom": [15, 8], "anchor": "year"},
               {"wipe": ["y2022", "y2026"], "zoom": [8, 6], "family": "w", "min_s": 4, "anchor": "year"}, {"asset": "y2026", "zoom": [6, 3]}]
        plan, _ = sb.build(self.ep(vis), self.d, self.vm)
        by = {s["info"]: s for s in plan["shots"]}
        self.assertAlmostEqual(by["y2022"]["start"], 10.0 - 0.15, places=1)           # word 20 starts at 10.0 s
        wipe = by["wipe y2022->y2026"]
        reveal = wipe["start"] + wipe["layers"][1]["t"][0]
        self.assertAlmostEqual(reveal, 14.0, places=1)                                  # the reveal of 2026 begins at the word "2026" (14.0 s)
        self.assertTrue(plan["anchors"]["one"])

    def test_without_the_flag_nothing_moves(self):
        vis = [{"asset": "y2020", "zoom": [20, 12]}, {"asset": "y2022", "zoom": [15, 8]}, {"asset": "y2026", "zoom": [6, 3]}]
        plan, _ = sb.build(self.ep(vis), self.d, self.vm)
        self.assertEqual(plan["anchors"], {})

    def test_unspoken_year_is_reported_not_forced(self):
        vis = [{"asset": "y2020", "zoom": [20, 12]}, {"asset": "y2020", "zoom": [15, 8]}, {"asset": "y2022", "zoom": [6, 3], "anchor": "year"}]
        self.assertTrue(sb.anchor_durations(vis, [8, 6, 6], [{"w0": 0, "n": 2, "text": "no years here"}], lambda i: i, 0, 20, lambda v: 2.5)[1][0]["status"])

    def test_long_wipe_slot_is_one_reveal_not_a_repeat(self):
        vis = [{"asset": "y2020", "zoom": [20, 12]}, {"wipe": ["y2022", "y2026"], "zoom": [8, 6], "family": "w", "min_s": 4}]
        plan, _ = sb.build(self.ep(vis), self.d, self.vm)          # 20 s chapter: the wipe slot is long enough to split
        wipes = [x for x in plan["shots"] if any(L["type"] == "wipe" for L in x["layers"])]
        self.assertEqual(len(wipes), 1)
        self.assertGreater(len([x for x in plan["shots"] if x["info"] == "y2026"]), 0)

    def test_graphics_keep_their_time_when_anchors_stretch_the_gap(self):
        self.assets["g"] = {"src": "g.png", "kind": "graphic"}
        vis = [{"asset": "g", "kind": "graphic", "min_s": 3.5}, {"asset": "y2020", "zoom": [20, 12]}, {"asset": "y2022", "zoom": [15, 8], "anchor": "year"}]
        plan, _ = sb.build(self.ep(vis), self.d, self.vm)
        self.assertAlmostEqual(plan["shots"][0]["dur"], 3.5, places=1)

    def test_graphic_appears_when_its_claim_is_spoken_not_at_chapter_start(self):
        """EP005 render review: the 'What was reported' graphic sat under a sentence about buildings because its claim is made at the END of the chapter."""
        import json
        self.assets["g"] = {"src": "g.png", "kind": "graphic", "claims": ["C3"]}
        text = "## one: One\n" + " ".join(["w"] * 20) + " first. {L}\n" + " ".join(["x"] * 19) + " It is only compatible with Semafor. {C3}\n"
        open(os.path.join(self.d, "script.md"), "w").write(text)
        vis = [{"asset": "y2020", "zoom": [20, 12]}, {"asset": "g", "kind": "graphic", "min_s": 4, "claims": ["C3"], "anchor": "claim"}, {"asset": "y2022", "zoom": [15, 8]}]
        plan, _ = sb.build(self.ep(vis), self.d, {"words": [{"text": "w", "start": i / 2, "end": i / 2 + .4} for i in range(len(" ".join(["w"] * 20 + ["first."] + ["x"] * 19 + ["It", "is", "only", "compatible", "with", "Semafor."]).split()))]})
        g = next(x for x in plan["shots"] if x["info"] == "g")
        self.assertAlmostEqual(g["start"], 21 * 0.5 - 0.3, places=1)               # the C3 sentence begins at word 21 (10.5 s); the graphic leads it by 0.3 s
        self.assertNotEqual(plan["shots"][0]["info"], "g")

    def test_graphics_get_push_and_captions_are_kinetic(self):
        import json
        vis = [{"asset": "g", "kind": "graphic", "min_s": 4}, {"asset": "y2020", "zoom": [12, 6]}]
        self.assets["g"] = {"src": "g.png", "kind": "graphic"}
        plan, _ = sb.build(self.ep(vis), self.d, self.vm)
        tl = sb.to_timeline(self.ep(vis), plan, self.d, {"src": "n.wav", "meta": "n.json"}, "c.srt")
        self.assertGreater(tl["shots"][0]["layers"][0]["push"], 0)
        self.assertEqual(tl["captions"]["style"], "kinetic")


if __name__ == "__main__":
    unittest.main()
