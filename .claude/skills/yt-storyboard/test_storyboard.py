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

    def test_graphic_prefers_the_claim_sentence_that_names_its_year(self):
        """EP005 final review: the annotated 2026 hero graphic appeared under 'In October 2022 and 2023, nothing dark is here' because both sentences cite the same claim."""
        self.assets["g"] = {"src": "g.png", "kind": "graphic", "claims": ["C10"]}
        text = "## one: One\n" + " ".join(["w"] * 10) + " In 2022 nothing dark here. {C10}\n" + " ".join(["x"] * 10) + " By 2026 it is still there. {C10}\n"
        open(os.path.join(self.d, "script.md"), "w").write(text)
        words = [{"text": "w", "start": i / 2, "end": i / 2 + .4} for i in range(10 + 5 + 10 + 6)]
        vis = [{"asset": "y2020", "zoom": [20, 12]}, {"asset": "g", "kind": "graphic", "min_s": 4, "claims": ["C10"], "anchor": "claim", "anchor_year": "2026"}, {"asset": "y2022", "zoom": [15, 8]}]
        plan, _ = sb.build(self.ep(vis), self.d, {"words": words})
        g = next(x for x in plan["shots"] if x["info"] == "g")
        self.assertAlmostEqual(g["start"], 15 * 0.5 - 0.3, places=1)           # the 2026 sentence begins at word 15 (7.5 s); the 2022 sentence (word 0) was not chosen

    def test_a_graphic_is_never_squeezed_unreadable_by_the_next_anchor(self):
        """EP005 final render: the annotated hero graphic got 2 s because the wipe anchored on the word '2026' two seconds after it."""
        self.assets["g"] = {"src": "g.png", "kind": "graphic", "claims": ["C10"]}
        text = "## one: One\n" + " ".join(["w"] * 10) + " In 2025 and 2026 it is still there. {C10}\n" + " ".join(["x"] * 10) + "\n"
        open(os.path.join(self.d, "script.md"), "w").write(text)
        words = [{"text": "w", "start": i / 2, "end": i / 2 + .4} for i in range(10 + 8 + 10)]
        vis = [{"asset": "y2020", "zoom": [20, 12]}, {"asset": "g", "kind": "graphic", "min_s": 6, "claims": ["C10"], "anchor": "claim"},
               {"wipe": ["y2022", "y2026"], "zoom": [8, 6], "family": "w", "min_s": 4, "anchor": "year"}, {"asset": "y2026", "zoom": [6, 3]}]
        plan, _ = sb.build(self.ep(vis), self.d, {"words": words})
        g = next(x for x in plan["shots"] if x["info"] == "g")
        self.assertGreaterEqual(g["dur"], 3.5)

    def test_graphics_get_push_and_captions_are_kinetic(self):
        import json
        vis = [{"asset": "g", "kind": "graphic", "min_s": 4}, {"asset": "y2020", "zoom": [12, 6]}]
        self.assets["g"] = {"src": "g.png", "kind": "graphic"}
        plan, _ = sb.build(self.ep(vis), self.d, self.vm)
        tl = sb.to_timeline(self.ep(vis), plan, self.d, {"src": "n.wav", "meta": "n.json"}, "c.srt")
        self.assertGreater(tl["shots"][0]["layers"][0]["push"], 0)
        self.assertEqual(tl["captions"]["style"], "kinetic")


    def test_build_steps_can_sit_in_one_tagged_sentence(self):
        """EP005 checks chapter: 'First, was it a one-day accident? No. The segment appears on three dates...' is ONE tagged sentence holding three steps."""
        self.assets["g_s1"] = {"src": "a", "kind": "graphic", "claims": [], "exempt": True}
        self.assets["g"] = {"src": "b", "kind": "graphic", "claims": [], "exempt": True}
        text = "## one: One\n" + " ".join(["w"] * 19) + " end.\nAlpha beta " + " ".join(["w"] * 3) + " gamma delta " + " ".join(["x"] * 14) + ". {C1}\n"
        open(os.path.join(self.d, "script.md"), "w").write(text)
        words = [{"text": "w", "start": i / 2, "end": i / 2 + .4} for i in range(20 + 2 + 3 + 2 + 14)]
        vis = [{"asset": "y2020", "zoom": [20, 12]},
               {"asset": "g_s1", "kind": "graphic", "min_s": 6, "claims": [], "anchor": "claim", "anchor_text": "alpha beta",
                "steps": [{"asset": "g_s1", "anchor_text": "alpha beta"}, {"asset": "g", "anchor_text": "gamma delta"}]},
               {"asset": "y2022", "zoom": [15, 8]}]
        plan, _ = sb.build(self.ep(vis), self.d, {"words": words})
        g = next(x for x in plan["shots"] if x["info"] == "g_s1")
        extra = next(L for L in g["layers"] if L.get("asset") == "g")
        self.assertAlmostEqual(g["start"] + extra["t"][0], 25 * 0.5 - 0.2, places=1)       # "gamma" is word 25 (12.5 s), inside the same sentence

    def test_anchor_text_places_a_graphic_and_each_build_step_at_its_own_words(self):
        """EP005 visual revision: scenes written in notes.json are tied to the sentence they illustrate, and a stepped card builds as the narrator speaks."""
        self.assets["g_s1"] = {"src": "g.s1.png", "kind": "graphic", "claims": [], "exempt": True}
        self.assets["g"] = {"src": "g.png", "kind": "graphic", "claims": [], "exempt": True}
        text = "## one: One\n" + " ".join(["w"] * 19) + " end.\nAlpha beta " + " ".join(["w"] * 5) + " done.\nGamma delta " + " ".join(["x"] * 14) + ".\n"
        open(os.path.join(self.d, "script.md"), "w").write(text)
        words = [{"text": "w", "start": i / 2, "end": i / 2 + .4} for i in range(20 + 2 + 6 + 2 + 14)]
        vis = [{"asset": "y2020", "zoom": [20, 12]},
               {"asset": "g_s1", "kind": "graphic", "min_s": 6, "claims": [], "anchor": "claim", "anchor_text": "alpha beta",
                "steps": [{"asset": "g_s1", "anchor_text": "alpha beta"}, {"asset": "g", "anchor_text": "gamma delta"}]},
               {"asset": "y2022", "zoom": [15, 8]}]
        plan, _ = sb.build(self.ep(vis), self.d, {"words": words})
        g = next(x for x in plan["shots"] if x["info"] == "g_s1")
        self.assertAlmostEqual(g["start"], 20 * 0.5 - 0.3, places=1)                  # "alpha" is word 20 (10.0 s); the card leads it by 0.3 s
        extra = [L for L in g["layers"] if L.get("asset") == "g"]
        self.assertEqual(len(extra), 1)
        self.assertAlmostEqual(g["start"] + extra[0]["t"][0], 28 * 0.5 - 0.2, places=1)   # the second build step arrives as the "Gamma" line begins (word 28, 14.0 s)
        self.assertGreater(extra[0]["push"], 0)


class NoQuota(unittest.TestCase):
    def mono(self, chapter):
        return {"chapters": {"c": [0, 45]}, "shots": [{"id": f"s{i}", "chapter": chapter, "start": i * 5.0, "dur": 5.0, "layers": [{"type": "image"}], "camera": {"to": {"width_km": 8}}} for i in range(9)]}

    def test_long_map_run_needs_a_stated_reason_not_a_photo(self):
        d = sb.diversity(self.mono("c"), {})
        self.assertEqual(d["status"], "WARN")
        self.assertTrue(any("visual_choices" in w for w in d["warnings"]))
        ok = sb.diversity(self.mono("c"), {"visual_choices": {"c": "the measurement itself is the evidence: only the satellite frames show the change"}})
        self.assertEqual(ok["status"], "OK")

    def test_no_photo_quota_exists(self):
        d = sb.diversity({"chapters": {}, "shots": [{"id": "a", "chapter": "c", "start": 0, "dur": 5, "layers": [{"type": "graphic"}]}, {"id": "b", "chapter": "c", "start": 5, "dur": 5, "layers": [{"type": "image"}], "camera": {"to": {"width_km": 3}}}]}, {})
        self.assertEqual(d["status"], "OK")
        self.assertFalse(any("no photo" in w for w in d["warnings"]))


class Media(unittest.TestCase):
    def setUp(self):
        import tempfile, json
        self.d = tempfile.mkdtemp()
        json.dump(GRID, open(os.path.join(self.d, "grid.json"), "w"))
        open(os.path.join(self.d, "script.md"), "w").write("## one: One\n" + "word " * 70 + "\n")
        self.assets = {"a": {"src": "a.png"}, "m_p": {"src": "media/assets/p.jpg", "kind": "external_still", "label": "Shore", "credit": "Shore / A / PD", "source_url": "https://example.org/p",
                                                       "license": "Public Domain", "retrieved": "2026-10-21", "media_id": "p", "claims": []}}

    def ep(self, vis, **k):
        return dict({"grid": "grid.json", "focus": [35.215, 28.11], "assets": self.assets, "chapters": [{"id": "one", "visuals": vis}]}, **k)

    def test_still_is_a_full_frame_shot_with_fixed_time_and_its_provenance_reaches_the_timeline(self):
        vis = [{"asset": "a", "zoom": [12, 6]}, {"asset": "m_p", "kind": "still", "min_s": 5, "info": "photo"}, {"asset": "a", "zoom": [6, 12]}]
        ep = self.ep(vis)
        plan, labels = sb.build(ep, self.d)
        st = next(x for x in plan["shots"] if x["layers"][0]["type"] == "still")
        self.assertAlmostEqual(st["dur"], 5.0, places=1)
        self.assertNotIn("camera", st)
        tl = sb.to_timeline(ep, plan, self.d)
        self.assertNotIn("media_id", tl["assets"]["m_p"])
        self.assertEqual(tl["assets"]["m_p"]["license"], "Public Domain")

    def test_video_is_a_full_frame_shot_with_its_trim_and_kept_time(self):
        self.assets["m_v"] = {"src": "media/assets/v.mp4", "kind": "video", "label": "Time-lapse", "credit": "NASA / SVS", "media_id": "v", "claims": []}
        vis = [{"asset": "a", "zoom": [12, 6]}, {"asset": "m_v", "kind": "video", "min_s": 8, "trim": 3.0}, {"asset": "a", "zoom": [6, 12]}]
        ep = self.ep(vis)
        plan, _ = sb.build(ep, self.d)
        v = next(x for x in plan["shots"] if x["layers"][0]["type"] == "video")
        self.assertAlmostEqual(v["dur"], 8.0, places=1)
        self.assertEqual(v["layers"][0]["trim"], 3.0)
        self.assertNotIn("media_id", sb.to_timeline(ep, plan, self.d)["assets"]["m_v"])

    def test_rendering_label_is_drawn_and_exempt_from_claim_matching(self):
        vis = [{"asset": "a", "zoom": [12, 6]}, {"asset": "m_p", "kind": "still", "min_s": 5, "label": {"text": "ARTIST'S RENDERING"}}]
        plan, labels = sb.build(self.ep(vis), self.d)
        lab = next(l for l in labels if l["text"] == "ARTIST'S RENDERING")
        self.assertTrue(lab["exempt"])

    def test_diversity_flags_a_wall_of_satellite_maps_and_credits_variety(self):
        mono = {"shots": [{"id": f"s{i}", "start": i * 5.0, "dur": 5.0, "layers": [{"type": "image"}], "camera": {"to": {"width_km": 8}}} for i in range(9)]}
        d = sb.diversity(mono)
        self.assertEqual(d["status"], "WARN")
        self.assertEqual(d["longest_map_run"]["shots"], 9)
        mixed = {"shots": [{"id": f"s{i}", "start": i * 5.0, "dur": 5.0, "layers": [{"type": ["image", "image", "still", "graphic"][i % 4]}],
                            "camera": {"to": {"width_km": [14, 6, 3, 8][i % 4]}}} for i in range(12)]}
        m = sb.diversity(mixed)
        self.assertEqual(m["status"], "OK")
        self.assertGreater(m["kind_share"]["still"], 0.2)


if __name__ == "__main__":
    unittest.main()
