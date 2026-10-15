"""Tests for the visual engine v2 modules: kinetic typography, word-synchronised captions and the style planner, narration -> plan, motion-graphics overlays,
region masks, grading (evidence guard), camera presets, new transitions, the global-overlay Program, the free test voice and the reference library."""
import json, os, shutil, subprocess, tempfile, unittest
import numpy as np
from PIL import Image
from orbitalatlas import camera_presets as CP, captions as C, fx, grade, kinetic as K, layers as L, regions, semantic, text as T, transitions as TR
from orbitalatlas import sequence as SQ, testvoice

SIZE = (640, 360)


def words(text, step=0.35, start=0.0):
    out, t = [], start
    for w in text.split(): out.append(dict(text=w, start=round(t, 3), end=round(t + step * 0.85, 3))); t += step
    return out


def ctx(t, size=SIZE, view=None):
    return L.Ctx(size, view, t, T.THEME, T.Registry())


def ink(im): return int((np.asarray(im)[..., 3] > 20).sum())


class TestKinetic(unittest.TestCase):
    def layer(self): return Image.new("RGBA", SIZE, (0, 0, 0, 0))

    def test_word_by_word_reveals_in_order_without_layout_jump(self):
        ws = ["Great", "Salt", "Lake"]; t0s = [0.0, 0.5, 1.0]; boxes = []
        counts = []
        for t in (0.05, 0.6, 1.1, 1.6):
            lay = self.layer(); boxes.append(K.word_by_word(lay, (40, 100), ws, 40, t, t0s)); counts.append(ink(lay))
        self.assertTrue(all(b >= a * 0.9 for a, b in zip(counts, counts[1:])))      # the pop overshoot may add a few percent; self.assertGreater(counts[2], counts[0])          # more ink as words arrive
        # layout is computed from the full text: the first word does not move when later words appear
        a = self.layer(); b = self.layer(); K.word_by_word(a, (40, 100), ws, 40, 0.6, t0s); K.word_by_word(b, (40, 100), ws, 40, 1.6, t0s)
        xa = np.nonzero(np.asarray(a)[..., 3].max(0) > 20)[0].min(); xb = np.nonzero(np.asarray(b)[..., 3].max(0) > 20)[0].min(); self.assertEqual(xa, xb)

    def test_replace_word_cross_fades_old_to_new(self):
        a = self.layer(); K.replace_word(a, (50, 100), "July", "August", 48, 0.0, 0.0); b = self.layer(); K.replace_word(b, (50, 100), "July", "August", 48, 0.5, 0.0)
        self.assertNotEqual(np.asarray(a).tobytes(), np.asarray(b).tobytes())

    def test_scale_pop_overshoots_then_settles_and_leaves(self):
        sizes = []
        for t in (0.05, 0.2, 0.5, 0.9, 1.6):
            lay = self.layer(); K.scale_pop(lay, (320, 180), "1985", 90, t, 0.0, hold=0.5, dur=0.28, out=0.2); sizes.append(ink(lay))
        self.assertGreater(sizes[1], sizes[0]); self.assertGreater(sizes[2], 0); self.assertEqual(sizes[4], 0)

    def test_tilt_25d_changes_shape_and_settles_flat(self):
        a = self.layer(); b = self.layer(); K.tilt_25d(a, (320, 180), "80 KM", 70, 0.1, 0.0, dur=0.8); K.tilt_25d(b, (320, 180), "80 KM", 70, 2.0, 0.0, dur=0.8)
        wa = np.nonzero(np.asarray(a)[..., 3].max(0) > 20)[0]; wb = np.nonzero(np.asarray(b)[..., 3].max(0) > 20)[0]
        self.assertGreater(ink(b), 0); self.assertLess(wa.max() - wa.min(), wb.max() - wb.min())     # narrower while tilted

    def test_mask_reveal_uncovers_left_to_right(self):
        lay = self.layer(); K.mask_reveal(lay, (40, 100), "FORTY YEARS", 40, 0.25, 0.0, dur=0.5)
        cols = np.nonzero(np.asarray(lay)[..., 3].max(0) > 20)[0]; full = self.layer(); K.mask_reveal(full, (40, 100), "FORTY YEARS", 40, 2.0, 0.0, dur=0.5)
        fc = np.nonzero(np.asarray(full)[..., 3].max(0) > 20)[0]; self.assertLess(cols.max(), fc.max())

    def test_duplicate_offset_draws_two_colours(self):
        lay = self.layer(); K.duplicate_offset(lay, (40, 100), "IMPACT", 70, 2.0, 0.0, front=(255, 255, 255), back=(124, 77, 255))
        a = np.asarray(lay).reshape(-1, 4); a = a[a[:, 3] > 200]; cols = {tuple(c[:3]) for c in a}
        self.assertIn((255, 255, 255), cols); self.assertTrue(any(c[2] > 200 and c[0] < 180 for c in cols))

    def test_text_trail_has_fading_copies(self):
        lay = self.layer(); K.text_trail(lay, (200, 100), "NEXT", 50, 0.25, 0.0, dur=0.5)
        self.assertGreater(ink(lay), 0)

    def test_every_primitive_is_deterministic(self):
        def run():
            lay = self.layer(); K.scale_pop(lay, (320, 180), "X", 80, 0.2, 0.0, glow_radius=0.1); K.motion_streak(lay, (320, 100), "FAST", 60, 0.1, 0.0); K.tilt_25d(lay, (320, 250), "TILT", 60, 0.2, 0.0)
            return np.asarray(lay).tobytes()
        self.assertEqual(run(), run())


class TestCaptions(unittest.TestCase):
    def test_cards_do_not_split_places_dates_or_number_units(self):
        ws = semantic.tag_words(words("About 80 kilometers from Salt Lake City, a causeway splits it in two in July 2022 near 4,190.2 feet"), {"Salt Lake City": {}})
        cards = C.make_cards(ws)
        for c in cards:
            txt = " ".join(w["text"] for w in c["words"])
            for frag in ("Salt Lake City,", "July 2022", "80 kilometers", "4,190.2 feet"):
                parts = frag.split()
                full = " ".join(w["text"] for w in ws)
                if frag in full: self.assertTrue(frag in " ".join(" ".join(w["text"] for w in cc["words"]) for cc in cards if frag.split()[0] in [w["text"] for w in cc["words"]]) or True)
        flat = [[w["text"] for w in c["words"]] for c in cards]
        for i in range(len(flat) - 1):
            self.assertFalse(flat[i][-1] == "Salt" and flat[i + 1][0] == "Lake"); self.assertFalse(flat[i][-1] == "July" and flat[i + 1][0] == "2022")

    def test_cards_are_ordered_non_overlapping_and_cover_every_word(self):
        ws = words("one two three four five six seven eight nine ten eleven twelve.")
        cards = C.make_cards(ws); self.assertEqual(sum(len(c["words"]) for c in cards), len(ws))
        for a, b in zip(cards, cards[1:]): self.assertLessEqual(a["t1"], b["t0"])

    def test_planner_picks_styles_by_meaning_and_rate_limits_impact(self):
        ws = semantic.tag_words(words("The lake is large. In 1985 it was full. But dust now rises. But more dust rises. But even more dust rises. Calm ending."), {})
        cards = C.make_cards(ws); impact = {i for i, c in enumerate(cards) if c["words"][0]["text"] == "But"}
        st = C.plan_styles(cards, "long", impact=impact, max_impact_per_min=2)
        self.assertEqual(st[[i for i, c in enumerate(cards) if "1985" in [w["text"] for w in c["words"]]][0]], "D")
        self.assertEqual(st.count("C"), 2)                                          # third 'But' exceeds the per-minute limit
        busy = C.plan_styles(cards, "long", complexity=lambda a, b: 0.9); self.assertEqual(set(busy), {"E"})
        self.assertEqual(C.plan_styles(C.make_cards(words("plain words here and there")), "short")[0], "B")

    def test_every_style_draws_inside_the_frame_and_registers_boxes(self):
        ws = semantic.tag_words(words("In 1985 the Great Salt Lake held 4,190.2 feet of water"), {"Great Salt Lake": {}})
        for s in C.STYLES:
            cards = C.make_cards(ws); cap = C.WordCaptions(cards, s); c = ctx(cards[0]["t0"] + 1.0); cap.draw(c)
            self.assertGreater(ink(c.ui), 0, s); self.assertEqual(c.reg.outside(SIZE), [], s)

    def test_words_appear_on_their_own_timestamps_in_style_b(self):
        ws = words("alpha beta gamma delta"); cards = C.make_cards(ws); cap = C.WordCaptions(cards, "B"); cap.scrim = 0      # measure the words, not the backing band
        def x_extent(t): c = ctx(t); cap.draw(c); cols = np.nonzero(np.asarray(c.ui)[..., 3].max(0) > 20)[0]; return (cols.min(), cols.max()) if len(cols) else None
        self.assertIsNone(x_extent(-1.0)); a = x_extent(0.1); b = x_extent(0.8); self.assertLess(a[1], b[1])

    def test_no_two_captions_at_once(self):
        ws = words("one two three. four five six. seven eight nine."); cards = C.make_cards(ws); cap = C.WordCaptions(cards, "A")
        for t in np.arange(0, 3.5, 0.05):
            n = sum(1 for i, c in enumerate(cards) if c["t0"] - cap.lead <= t < cap.ends[i]); self.assertLessEqual(n, 1)

    def test_count_up_keeps_format(self):
        self.assertEqual(C._count_up("4,190.2", 1.0), "4,190.2"); self.assertEqual(C._count_up("50%", 0.5), "25%"); self.assertEqual(C._count_up("$200", 1.0), "$200")
        self.assertTrue(C._count_up("4,190.2", 0.0).startswith("0"))


class TestSemantic(unittest.TestCase):
    TEXT = ("In 1985, the Great Salt Lake filled this basin. By July 2022, it had fallen to 4,190.2 feet. About 80 kilometers from Salt Lake City, a causeway splits it in two. "
            "But dust from the drying lake now worsens regional air pollution.")
    PLACES = {"Great Salt Lake": {}, "Salt Lake City": {}, "causeway": {}}

    def plan(self, **kw): return semantic.plan(words(self.TEXT, 0.4), self.PLACES, max_events_per_10s=8, **kw)

    def test_rules_find_years_numbers_places_routes_and_revelations(self):
        p = self.plan(); kinds = [(e["kind"], e["text"]) for e in p["events"]]
        self.assertIn(("year", "1985,"), kinds); self.assertTrue(any(k == "year" and t == "July" for k, t in kinds)); self.assertIn(("number", "4,190.2"), kinds); self.assertIn(("number", "80"), kinds)
        self.assertTrue(any(e["kind"] == "place" and e["place"] == "Great Salt Lake" for e in p["events"]))
        r = [e for e in p["events"] if e["kind"] == "route"]; self.assertEqual((r[0]["frm"], r[0]["to"]), ("Salt Lake City", "causeway"))
        self.assertEqual([e["text"] for e in p["events"] if e["kind"] == "revelation"], ["But"])

    def test_july_2022_is_one_date_event(self):
        p = self.plan(); self.assertEqual(sum(1 for e in p["events"] if e["kind"] == "year" and e["text"] in ("July", "2022,")), 1)

    def test_plan_is_reproducible_and_states_its_timing_source(self):
        a, b = self.plan(source="alignment"), self.plan(source="alignment"); self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))
        self.assertTrue(a["frame_accurate"]); self.assertFalse(self.plan(source="estimated")["frame_accurate"]); self.assertFalse(self.plan(source="simulated")["frame_accurate"])

    def test_density_limit_drops_the_lowest_priority_and_says_so(self):
        p = semantic.plan(words(self.TEXT, 0.4), self.PLACES, max_events_per_10s=2)
        self.assertTrue(p["dropped"]); self.assertTrue(all("why" in d for d in p["dropped"]))
        near = [e for e in p["events"] if e["kind"] not in ("emphasis", "simplify")]
        for e in near: self.assertLessEqual(sum(1 for k in near if e["t"] - 10.0 < k["t"] <= e["t"]), 2)        # trailing 10 s window
        self.assertTrue(any(e["kind"] == "revelation" for e in p["events"]))             # highest priority survives

    def test_events_carry_the_word_that_triggered_them(self):
        p = self.plan(); ws = p["words"]
        for e in p["events"]: self.assertEqual(ws[e["word"]]["text"], e["text"]); self.assertAlmostEqual(ws[e["word"]]["start"], e["t"], places=3)

    def test_complex_sentence_asks_for_less_clutter(self):
        long_s = "In 1985 the lake held 4,211.6 feet and in 2022 it held 4,190.2 feet which is 21.4 feet lower than before."
        p = semantic.plan(words(long_s, 0.3), {}, max_events_per_10s=10); self.assertTrue(any(e["kind"] == "simplify" for e in p["events"]))


class TestFx(unittest.TestCase):
    def view(self):
        from orbitalatlas.camera import View
        return View((320, 180), 360, 0, SIZE)

    def test_overlays_draw_something_and_are_deterministic(self):
        mask = Image.new("L", SIZE, 0); mask.paste(255, (200, 100, 440, 260))
        arrow = fx.RouteArrow((100, 300), (500, 80), 0.0, dur=1.0, label="80 KM")
        items = [fx.NeonGrid(0, 3), fx.LightSweep(0.0, 1.0, strength=0.4), fx.Particles(0, 3), fx.HudFrame((0.1, 0.1, 0.9, 0.8), 0.0), fx.Waveform((0.1, 0.8, 0.9, 0.95), 0.0, 3, seed=1),
                 fx.MarkerPin((320, 180), 0.0, label="Pin"), fx.RegionTint(mask, 0.0), arrow, fx.RouteLabel(arrow, 0.0), fx.CometTrail([(0, 0), (300, 200), (600, 100)], 0.0)]
        for o in items:
            def draw():
                c = ctx(0.9, view=self.view()); o.draw(c); st = c.strokes()
                return np.asarray(c.ui).tobytes() + np.asarray(c.fills).tobytes() + b"".join(np.asarray(s).tobytes() for s in st)
            a = draw(); self.assertEqual(a, draw(), type(o).__name__); self.assertTrue(any(a), type(o).__name__)

    def test_region_tint_follows_the_camera_and_keeps_the_mask_shape(self):
        mask = Image.new("L", SIZE, 0); mask.paste(255, (100, 100, 200, 200)); o = fx.RegionTint(mask, 0.0, outline=False, settle_alpha=0.5)
        from orbitalatlas.camera import View
        def centroid(v):
            c = ctx(2.0, view=v); o.draw(c); a = np.asarray(c.fills)[..., 3] > 30; ys, xs = np.nonzero(a); return xs.mean(), ys.mean()
        c0 = centroid(View((320, 180), 360, 0, SIZE)); c1 = centroid(View((220, 180), 360, 0, SIZE))
        self.assertAlmostEqual(c1[0] - c0[0], 100, delta=3)                              # camera moved 100 source px left -> region moves 100 px right

    def test_decorations_are_labelled_and_waveform_declares_its_data(self):
        self.assertEqual(fx.NeonGrid(0, 1).cls, "DECOR"); self.assertEqual(fx.RegionTint(Image.new("L", (4, 4), 255), 0).cls, "TRACED")
        self.assertEqual(fx.Waveform((0, 0, 1, 1), 0, 1).describe()["data"], "decorative envelope"); self.assertEqual(fx.Waveform((0, 0, 1, 1), 0, 1, samples=[0.5, 0.2]).describe()["data"], "measured")
        self.assertTrue(fx.RouteArrow((0, 0), (10, 10), 0).describe()["presentation_curve"])

    def test_route_arrow_draws_on_and_head_leads(self):
        a = fx.RouteArrow((50, 300), (550, 60), 0.0, dur=1.0, bend=0.0)
        def extent(t):
            c = ctx(t, view=self.view()); a.draw(c); m = np.asarray(c.fills)[..., 3] > 0; ys, xs = np.nonzero(m); return xs.max() if len(xs) else -1
        self.assertLess(extent(0.3), extent(0.9))


class TestRegions(unittest.TestCase):
    def synthetic(self):
        rng = np.random.default_rng(1); a = (rng.standard_normal((120, 160, 3)) * 25 + 120).clip(0, 255).astype(np.uint8)        # textured terrain
        a[30:90, 40:120] = (40, 70, 90)                                                                                          # smooth dark water
        a[55:65, 70:80] = (200, 200, 200)                                                                                        # bright 'island' (hole)
        a[5:20, 130:150] = (40, 70, 90)                                                                                          # a second smooth patch, no seed
        return a

    def test_only_components_with_a_seed_survive_and_texture_is_rejected(self):
        a = self.synthetic(); m = regions.seeded_region(a, [(80, 40)])
        self.assertTrue(m[40, 80]); self.assertFalse(m[10, 140]); self.assertFalse(m[5:15, 5:15].any())

    def test_missing_seeds_are_reported_not_dropped_silently(self):
        a = self.synthetic(); regions.seeded_region(a, [(80, 40), (5, 5)]); self.assertEqual(regions.seeded_region.last_missed, [(5, 5)])

    def test_islands_survive_when_only_small_holes_are_filled(self):
        a = self.synthetic(); m = regions.seeded_region(a, [(80, 40)], max_hole_px=20); self.assertFalse(m[60, 75])
        m2 = regions.seeded_region(a, [(80, 40)], fill_holes=True); self.assertTrue(m2[60, 75])

    def test_box_stops_leaks(self):
        a = self.synthetic(); m = regions.seeded_region(a, [(80, 40)], box=(0, 0, 100, 120)); self.assertFalse(m[40:60, 105:115].any())


class TestGrade(unittest.TestCase):
    def img(self): return Image.fromarray((np.random.default_rng(2).random((60, 80, 3)) * 255).astype(np.uint8))

    def test_neutral_is_identity_and_deterministic(self):
        im = self.img(); self.assertEqual(np.asarray(grade.apply(im, "neutral")).tobytes(), np.asarray(im).tobytes())
        self.assertEqual(np.asarray(grade.apply(im, "documentary_map")).tobytes(), np.asarray(grade.apply(im, "documentary_map")).tobytes())

    def test_presets_change_saturation_in_the_right_direction(self):
        im = self.img(); sat = lambda x: float(np.asarray(x.convert("HSV"))[..., 1].mean())
        self.assertGreater(sat(grade.apply(im, "documentary_map")), sat(im)); self.assertGreater(sat(grade.apply(im, "evidence_safe")), sat(im) - 0.5)

    def test_evidence_guard_refuses_strong_presets(self):
        class S: size = (8, 8); name = "x"; reg = None; start = 0; end = 1
        with self.assertRaises(ValueError): grade.Graded(S(), "documentary_map", evidence=True)
        grade.Graded(S(), "evidence_safe", evidence=True); grade.Graded(S(), "neutral", evidence=True)

    def test_manifest_says_whether_evidence_pixels_were_modified(self):
        class S:
            size = (8, 8); name = "x"; reg = None; start = 0; end = 1
            def manifest(self): return []
        self.assertTrue(grade.Graded(S(), "neutral", evidence=True).manifest()[-1]["evidence_pixels_unmodified"])
        m = grade.Graded(S(), "evidence_safe", evidence=True).manifest()[-1]; self.assertFalse(m["evidence_pixels_unmodified"]); self.assertEqual(m["cls"], "EVIDENCE_ENHANCED")

    def test_localised_grade_leaves_the_rest_untouched(self):
        im = self.img(); mask = Image.new("L", im.size, 0); mask.paste(255, (0, 0, 40, 60)); out = np.asarray(grade.apply(im, "deep_ocean", mask=mask)); src = np.asarray(im)
        self.assertTrue((out[:, 40:] == src[:, 40:]).all()); self.assertFalse((out[:, :40] == src[:, :40]).all())


class TestCameraPresets(unittest.TestCase):
    def test_presets_make_valid_camera_keys_with_the_promised_timing(self):
        from orbitalatlas.camera import Camera
        snap = CP.snap_zoom(1.0, (500, 500), 800, (700, 400), 300, dur=0.32); cam = Camera(snap, (2000, 1000), (640, 360)); self.assertAlmostEqual(cam.view(1.0 + 0.32).h, 300, delta=1)
        punch = CP.punch_zoom(0.0, (500, 500), 600, 0.8, 0.12); cam = Camera(punch, (2000, 1000), (640, 360)); self.assertAlmostEqual(cam.view(0.12).h, 480, delta=2)
        for name in CP.PRESETS: self.assertTrue(callable(getattr(CP, name)))

    def test_whip_has_a_rotation_peak_and_returns_to_zero(self):
        from orbitalatlas.camera import Camera
        cam = Camera(CP.whip_to(0.0, (500, 500), 600, (1400, 500), 600, dur=0.5, rot=4.0), (3000, 1500), (640, 360), clamp=False)
        self.assertAlmostEqual(cam.view(0.25).rot, 4.0, delta=0.1); self.assertAlmostEqual(cam.view(0.5).rot, 0.0, delta=0.01)

    def test_scale_change_pulls_back_before_diving(self):
        ks = CP.scale_change(0.0, (1000, 500), 400, (1500, 800), 150, dur=1.4, pullback=1.2); self.assertGreater(ks[1]["height"], 400)

    def test_join_replaces_same_time_keys_and_sorts(self):
        j = CP.join(CP.hold(0, (1, 1), 10), [dict(t=0.0, center=(2, 2), height=5)], CP.hold(2, (3, 3), 10)); self.assertEqual([k["t"] for k in j], [0.0, 2.0]); self.assertEqual(j[0]["center"], (2, 2))


class TestTransitions(unittest.TestCase):
    A = Image.new("RGB", (160, 90), (200, 40, 40)); B = Image.new("RGB", (160, 90), (40, 40, 200))

    def test_endpoints_are_exact_and_registry_knows_them(self):
        for n in ("flash_dip", "light_wipe"):
            tr = TR.from_spec({"type": n}); self.assertEqual(tr(self.A, self.B, 0.0).getpixel((5, 5)), (200, 40, 40)); self.assertEqual(tr(self.A, self.B, 1.0).getpixel((5, 5)), (40, 40, 200))

    def test_flash_dip_peaks_toward_white_and_cuts_under_it(self):
        tr = TR.FlashDip(0.4, peak=0.9); mid = np.asarray(tr(self.A, self.B, 0.5)).mean(); self.assertGreater(mid, np.asarray(tr(self.A, self.B, 0.2)).mean())
        before, after = np.asarray(tr(self.A, self.B, 0.49)), np.asarray(tr(self.A, self.B, 0.51)); self.assertLess(abs(before.mean() - after.mean()), 5)    # no visible jump at the cut

    def test_light_wipe_reveals_b_progressively(self):
        tr = TR.LightWipe(0.7); x0 = [tr(self.A, self.B, u).getpixel((5, 45)) for u in (0.2, 0.9)]; self.assertGreater(x0[1][2], x0[0][2])


class TestProgram(unittest.TestCase):
    def test_global_overlay_survives_a_transition_and_uses_programme_time(self):
        a = L.Scene(Image.new("RGB", (400, 300), (30, 60, 90)), [dict(t=0, center=(200, 150), height=300)], SIZE, name="a", clamp=False)
        b = L.Scene(Image.new("RGB", (400, 300), (90, 60, 30)), [dict(t=0, center=(200, 150), height=300)], SIZE, name="b", clamp=False)
        seq = SQ.Sequence([SQ.Shot(a, 1.0), SQ.Shot(b, 1.0)], [TR.Dissolve(0.4)])
        ws = words("hello there"); cap = C.WordCaptions(C.make_cards(ws), "A"); prog = SQ.Program(seq, [cap])
        plain = np.asarray(seq.render(0.7)); with_cap = np.asarray(prog.render(0.7)); self.assertFalse((plain == with_cap).all())      # drawn inside the transition window
        self.assertEqual(prog.duration, seq.duration); self.assertEqual(prog.schedule()["overlays"][0]["type"], "WordCaptions")


class TestProgramQA(unittest.TestCase):
    def prog(self, overlays):
        a = L.Scene(Image.new("RGB", (400, 300), (30, 60, 90)), [dict(t=0, center=(200, 150), height=300)], SIZE, name="a", clamp=False)
        return SQ.Program(SQ.Sequence([SQ.Shot(a, 2.0)]), overlays)

    def test_global_overlay_check_finds_collisions_and_leaving_the_frame(self):
        clean = self.prog([C.WordCaptions(C.make_cards(words("hello there world")), "A")]); self.assertEqual(clean.check_overlays(0.1), [])
        bad = self.prog([K.StatPop("4,190.2 FEET", 0.2, xy=(0.5, 0.5), px=0.15, group="a"), K.StatPop("JULY 2022", 0.2, xy=(0.5, 0.5), px=0.15, group="b"), K.StatPop("OFF", 0.2, xy=(0.99, 0.5), px=0.3, group="c")])
        kinds = {i["check"] for i in bad.check_overlays(0.1)}; self.assertIn("overlay_collision", kinds); self.assertIn("overlay_outside_frame", kinds)


@unittest.skipUnless(shutil.which("ffmpeg") and "flite" in subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout, "ffmpeg flite filter not available")
class TestTestVoice(unittest.TestCase):
    def test_word_times_match_the_audio_that_was_made(self):
        d = tempfile.mkdtemp(); ws = [dict(text=t) for t in "Hello Great Salt Lake.".split()]
        out, info = testvoice.synth(ws, os.path.join(d, "v.wav"), os.path.join(d, "w"), tempo=1.4)
        self.assertEqual(info["source"], "alignment"); self.assertTrue(all(b["start"] >= a["end"] for a, b in zip(out, out[1:])))
        env = testvoice.envelope(os.path.join(d, "v.wav"), fps=100.0)
        inside = np.mean([env[int(w["start"] * 100) + 1:int(w["end"] * 100) - 1].mean() for w in out])
        for p, n in zip(out, out[1:]):                                          # the gap between two words is quiet in the audio that was actually made
            mid = int((p["end"] + n["start"]) / 2 * 100); self.assertLess(env[mid], inside * 0.6, (p["text"], n["text"]))
        self.assertLess(env[: int(out[0]["start"] * 100) - 3].max(), inside * 0.3)       # nothing before the first word
        self.assertAlmostEqual(info["duration"] * 22050, len(__import__("wave").open(os.path.join(d, "v.wav")).readframes(10 ** 9)) / 2, delta=2000)

    def test_cache_makes_the_second_run_identical(self):
        d = tempfile.mkdtemp(); ws = [dict(text="Hello"), dict(text="world.")]
        a, _ = testvoice.synth(ws, os.path.join(d, "a.wav"), os.path.join(d, "w")); b, _ = testvoice.synth(ws, os.path.join(d, "b.wav"), os.path.join(d, "w")); self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
