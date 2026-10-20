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


if __name__ == "__main__":
    unittest.main()
