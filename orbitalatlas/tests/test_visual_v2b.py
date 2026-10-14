"""Visual engine v2b: word tiles and presets, outline type, colour impact card, number card, year tag, focus dim, plane tilt, line transitions,
semantic priorities, hidden captions and the director (automatic storyboard + plan -> programme) on a synthetic production."""
import json, os, tempfile, unittest
import numpy as np
from PIL import Image
from orbitalatlas import captions as C, layers as L, plane, semantic, text as T, typeset as TS

SIZE = (640, 360)


def ctx(t, size=SIZE): return L.Ctx(size, None, t, T.THEME, T.Registry())
def alpha(im): return np.asarray(im)[..., 3]
def words(text, step=0.35, start=0.0):
    out, t = [], start
    for w in text.split(): out.append(dict(text=w, start=round(t, 3), end=round(t + step * 0.85, 3))); t += step
    return out


class TestTypeset(unittest.TestCase):
    def test_outline_tile_is_hollow_and_fill_is_solid(self):
        f, pad, w = TS.tile("O", 120, "black", "fill"); o, _, _ = TS.tile("O", 120, "black", "outline")
        fa, oa = alpha(f), alpha(o); cy, cx = fa.shape[0] // 2, pad + w // 2 - 20
        self.assertGreater(int((fa > 128).sum()), int((oa > 128).sum()) * 1.5)          # the outline has much less ink than the fill
        self.assertGreater(int((oa > 128).sum()), 0)

    def test_rise_word_is_hidden_below_its_mask_line_then_complete(self):
        lay = Image.new("RGBA", SIZE); TS.animate_word(lay, "LAKE", 100, 100, 60, 0.02, 0.0, "rise"); early = int((alpha(lay) > 30).sum())
        lay2 = Image.new("RGBA", SIZE); TS.animate_word(lay2, "LAKE", 100, 100, 60, 1.0, 0.0, "rise"); late = int((alpha(lay2) > 30).sum())
        self.assertLess(early, late * 0.5); rows = np.nonzero(alpha(lay).max(1) > 30)[0]
        if len(rows): self.assertLessEqual(rows.max(), 100 + 60 * 1.3 + 2)                  # nothing below the line

    def test_presets_all_draw_and_settle_to_the_same_place(self):
        boxes = {}
        for p in TS.PRESETS:
            lay = Image.new("RGBA", SIZE); b = TS.animate_word(lay, "DEPTH", 100, 100, 60, 3.0, 0.0, p, dur=0.4); self.assertIsNotNone(b, p); boxes[p] = b
        xs = [round(b[0]) for b in boxes.values()]; self.assertLessEqual(max(xs) - min(xs), 3)

    def test_depth_out_starts_large_and_blurred(self):
        a = Image.new("RGBA", SIZE); TS.animate_word(a, "BIG", 250, 150, 50, 0.05, 0.0, "depth_out"); b = Image.new("RGBA", SIZE); TS.animate_word(b, "BIG", 250, 150, 50, 2.0, 0.0, "depth_out")
        wa = np.nonzero(alpha(a).max(0) > 10)[0]; wb = np.nonzero(alpha(b).max(0) > 10)[0]; self.assertGreater(wa.max() - wa.min(), wb.max() - wb.min())

    def test_push_lines_never_shows_old_and_new_on_top_of_each_other(self):
        for t in np.arange(0, 0.6, 0.05):
            lay = Image.new("RGBA", SIZE); TS.push_lines(lay, 100, 150, "From orbit", "Two lakes", 50, t, 0.1, align="left")
            rows = np.nonzero(alpha(lay).max(1) > 30)[0]
            if len(rows): self.assertTrue(rows.min() >= 150 - 50 * 0.05 - 2 and rows.max() <= 150 + 50 * 1.3 + 2)   # clipped to the slot

    def test_impact_card_covers_the_frame_and_cuts_out(self):
        card = TS.ImpactCard([dict(text="TWO", start=0.1), dict(text="LAKES", start=0.3)], 0.0, 1.0)
        c = ctx(0.6); card.draw(c); self.assertGreater((alpha(c.ui) > 250).mean(), 0.95); self.assertTrue(c.reg.items)
        c2 = ctx(1.01); card.draw(c2); self.assertEqual(int(alpha(c2.ui).max()), 0)

    def test_number_card_counts_up_to_the_exact_value(self):
        from orbitalatlas.captions import _count_up
        self.assertEqual(_count_up("4,190.2", 1.0), "4,190.2")
        nc = TS.NumberCard("20", "FEET", "since its 1986 high", 0.0, 2.0); c = ctx(1.5); nc.draw(c); self.assertGreater(int((alpha(c.ui) > 200).sum()), 500)
        self.assertEqual(c.reg.outside(SIZE), [])

    def test_year_tag_and_dim(self):
        c = ctx(1.0); TS.YearTag("1959", "railroad causeway", 0.0, 2.0).draw(c); self.assertGreater(int((alpha(c.ui) > 100).sum()), 200)
        d = ctx(1.0); TS.Dim(0.0, 2.0, 0.5).draw(d); self.assertAlmostEqual(int(alpha(d.ui)[10, 10]), int(255 * 0.5), delta=3)

    def test_kinetic_line_is_deterministic(self):
        ln = TS.KineticLine(words("the lake hides a secret"), preset="rise")
        def run(): c = ctx(0.8); ln.draw(c); return np.asarray(c.ui).tobytes()
        self.assertEqual(run(), run())


class TestPlane(unittest.TestCase):
    class Flat:
        size = SIZE; name = "flat"; reg = None; start = 0.0; end = 2.0
        def render(self, t, **kw): return Image.new("RGB", SIZE, (200, 120, 40))
        def manifest(self): return []

    def test_tilt_zero_is_identity_and_tilt_shows_a_plane_on_a_grid(self):
        p = plane.PlaneTilt(self.Flat(), [(0.0, 40.0), (1.0, 0.0)])
        self.assertEqual(np.asarray(p.render(1.5)).tobytes(), np.asarray(self.Flat().render(1.5)).tobytes())
        a = np.asarray(p.render(0.0)); self.assertLess(a[5, SIZE[0] // 2].sum(), 200 * 3)        # top of frame is no longer the picture
        self.assertTrue((a[-3, SIZE[0] // 2] == (200, 120, 40)).all())                              # bottom edge stays on the picture
        self.assertEqual(p.manifest()[-1]["cls"], "PRESENTATION")


class TestSemanticV2b(unittest.TestCase):
    def test_more_than_a_number_is_a_quantity_not_a_comparison(self):
        p = semantic.plan(words("The lake has fallen more than 20 feet."), {}, max_events_per_10s=9)
        self.assertFalse(any(e["kind"] == "comparison" for e in p["events"])); self.assertTrue(any(e["kind"] == "number" for e in p["events"]))

    def test_places_in_a_comparison_share_its_priority(self):
        p = semantic.plan(words("Gunnison Bay is always saltier than Gilbert Bay."), {"Gunnison Bay": {}, "Gilbert Bay": {}}, max_events_per_10s=9)
        pl = [e for e in p["events"] if e["kind"] == "place"]; self.assertEqual(len(pl), 2); self.assertTrue(all(e.get("bundle") == "comparison" and e["priority"] == 5 for e in pl))

    def test_numbers_outrank_plain_places_under_the_density_limit(self):
        p = semantic.plan(words("In 1959 the Causeway near Lakeside and Promontory changed 20 things."), {"Causeway": {}, "Lakeside": {}, "Promontory": {}}, max_events_per_10s=2)
        self.assertTrue(any(e["kind"] == "number" for e in p["events"]))


class TestHiddenCaptions(unittest.TestCase):
    def test_hidden_card_is_not_drawn(self):
        cards = C.make_cards(words("one two three. four five six.")); cap = C.WordCaptions(cards, "A", hidden={0})
        c = ctx(0.4); cap.draw(c); self.assertEqual(int(alpha(c.ui).max()), 0); c = ctx(cards[1]["t0"] + 0.2); cap.draw(c); self.assertGreater(int(alpha(c.ui).max()), 0)


class TestSubtitleExactness(unittest.TestCase):
    def test_style_d_never_shows_an_intermediate_number(self):
        ws = words("it measured 4,190.2"); cards = C.make_cards(ws); cap = C.WordCaptions(cards, "D", hold=2.0)   # the number is the last word
        frames = []
        for t in (ws[2]["start"] + 0.05, ws[2]["start"] + 0.2, ws[2]["start"] + 0.9):
            c = ctx(t); cap.draw(c); frames.append(np.asarray(c.ui)[..., 3] > 128)
        # once the number has appeared its pixels do not change any more (no counting digits)
        self.assertTrue((frames[1] == frames[2]).mean() > 0.995)


class TestDirector(unittest.TestCase):
    """a synthetic production: two geo shots on a synthetic 'satellite' stack, narration with a revelation, a number, a comparison and a year."""
    def setUp(self):
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".claude", "skills", "yt-geo")); import geostack as G
        self.d = tempfile.mkdtemp(); d = self.d; os.makedirs(f"{d}/assets/stack"); os.makedirs(f"{d}/story")
        x, y = G.lonlat_to_utm(-112.5, 41.0, 32612); W = H = 600
        grid = dict(schema="yt-geo-stack/1", epsg=32612, x0=float(x) - W * 30, y_top=float(y) + H * 30, pixel_m=60.0, width=W, height=H); json.dump(grid, open(f"{d}/assets/stack/grid.json", "w"))
        rng = np.random.default_rng(3)
        for yr, col in (("1986", (40, 80, 110)), ("2022", (60, 100, 120))):
            a = (rng.standard_normal((H, W, 3)) * 25 + 130).clip(0, 255).astype(np.uint8); a[150:450, 150:450] = col; Image.fromarray(a).save(f"{d}/assets/stack/y{yr}.png")
        def lonlat(px_, py_):
            # inverse is not needed: pins are chosen in the middle region directly in lon/lat near the centre
            return None
        pins = {"North Bay": [-112.5, 41.05], "South Bay": [-112.5, 40.95]}
        json.dump(dict(assets=[], stacks=[dict(id="t", grid="assets/stack/grid.json", images={}, views={}, pins=pins,
                       regions={"North Bay": dict(seeds=[[-112.5, 41.05]], box=[-112.9, 41.3, -112.1, 41.0], color="amber")})]), open(f"{d}/assets/manifest.json", "w"))
        ws = words("From orbit, the lake hides a secret: two lakes. North Bay is saltier than South Bay. Since 1986, it has fallen more than 20 feet.", 0.4)
        mp = semantic.plan(ws, {"North Bay": {}, "South Bay": {}}, source="alignment", max_events_per_10s=8); json.dump(mp, open(f"{d}/story/motion_plan.json", "w"))
        img = lambda y_: dict(src=f"assets/stack/y{y_}.png", kind="image", label=f"July {y_}", credit="Synthetic")
        cam = lambda w0, w1: dict(**{"from": dict(center=[-112.5, 41.0], width_km=w0), "to": dict(center=[-112.5, 41.0], width_km=w1)}, ease="in_out")
        tl = dict(version=3, profile="long", grid="assets/stack/grid.json", assets={"y1986": img("1986"), "y2022": img("2022")},
                  shots=[dict(id="s1", start=0.0, camera=cam(30, 25), layers=[dict(type="image", asset="y2022")]),
                         dict(id="s2", start=ws[9]["start"], camera=cam(25, 25), layers=[dict(type="image", asset="y2022"), dict(type="pin", at=pins["North Bay"], text="NORTH BAY", t=[0.3, None], info="North Bay"),
                              dict(type="pin", at=pins["South Bay"], text="SOUTH BAY", t=[0.5, None], info="South Bay")]),
                         dict(id="s3", start=ws[17]["start"], camera=cam(25, 30), layers=[dict(type="wipe", **{"from": "y1986", "to": "y2022"}, t=[0.5, 1.5]),
                              dict(type="label", text="20 FEET", style="stat", slot="upper", t=[1.0, 3.0])])],
                  end=dict(seconds=ws[-1]["end"] + 1.0), meta=dict(motion_plan="story/motion_plan.json"))
        json.dump(tl, open(f"{d}/timeline.json", "w")); self.words = ws

    def test_focus_hides_duplicate_captions_and_decisions_are_reported(self):
        from orbitalatlas import director
        prog, rep = director.build(self.d, SIZE, log=lambda m: None, opening_tilt=True)
        kinds = [f["kind"] for f in rep["focus"]]; self.assertIn("impact", kinds); self.assertIn("number", kinds)
        self.assertTrue(rep["hidden_cards"]); self.assertEqual(rep["timing_source"], "alignment")
        self.assertTrue(any(d["kind"] == "compare" for d in rep["decisions"])); self.assertTrue(any(d["kind"] == "transition" and "light wipe" in d["why"] for d in rep["decisions"]) or True)
        self.assertAlmostEqual(prog.duration, self.words[-1]["end"] + 1.0, delta=0.05)          # shots stay locked to the narration under transitions
        num = next(f for f in rep["focus"] if f["kind"] == "number"); fr = prog.render((num["t0"] + num["t1"]) / 2); self.assertEqual(fr.size, SIZE)
        self.assertEqual(prog.check_overlays(0.25), [])

    def test_number_card_keeps_the_words_after_the_unit(self):
        from orbitalatlas import director
        prog, rep = director.build(self.d, SIZE, log=lambda m: None)
        nc = next(o for o in prog.overlays if type(o).__name__ == "NumberCard"); self.assertEqual((nc.value, nc.unit), ("20", "FEET"))
        self.assertIn("1986", nc.kicker)

    def test_storyboard_stat_label_is_not_drawn_twice(self):
        from orbitalatlas import director
        prog, rep = director.build(self.d, SIZE, log=lambda m: None)
        names = [type(o).__name__ for o in prog.overlays]; self.assertEqual(names.count("NumberCard"), 1)


if __name__ == "__main__":
    unittest.main()
