"""v2c: keyword lift from the caption to the map, parallax labels and dust, punch-in, image date vs event year, adaptive intensity,
route rule, pacing report, and the synthesised sound design (cues, ducking margin, determinism, licence)."""
import os, tempfile, unittest, wave
import numpy as np
from PIL import Image
from orbitalatlas import captions as C, interact as IX, layers as L, semantic, sfx, text as T
from orbitalatlas.camera import View

SIZE = (640, 360)


def words(text, step=0.35, start=0.0):
    out, t = [], start
    for w in text.split(): out.append(dict(text=w, start=round(t, 3), end=round(t + step * 0.85, 3))); t += step
    return out


def ctx(t, view=None): return L.Ctx(SIZE, view, t, T.THEME, T.Registry())


def ink_centre(im):
    a = np.asarray(im)[..., 3] > 60; ys, xs = np.nonzero(a); return (xs.mean(), ys.mean()) if len(xs) else None


class TestInteract(unittest.TestCase):
    def setUp(self):
        self.ws = semantic.tag_words(words("water flows into Gilbert Bay to the south"), {"Gilbert Bay": {}}); self.cards = C.make_cards(self.ws)
        self.caps = C.WordCaptions(self.cards, "D"); self.view = View((500, 500), 360, 0, SIZE)

    def test_lift_starts_on_the_caption_word_and_lands_on_the_anchor(self):
        w = next(x for x in self.ws if x["text"] == "Gilbert"); box = self.caps.word_box(SIZE, *self.caps.locate(w["start"], "Gilbert"))
        lift = IX.KeywordLift(self.caps, w["start"], "Gilbert", (450, 420), 0.0, 9.0, label="Gilbert Bay", depth=0.0)
        c0 = ctx(w["start"] + 0.06, self.view); lift.draw(c0); s = ink_centre(c0.ui)
        self.assertLess(abs(s[1] - (box[1] + box[3]) / 2), 25)                                   # starts on the caption line
        c1 = ctx(w["start"] + 2.0, self.view); lift.draw(c1); e = ink_centre(c1.ui); a = self.view.pt((450, 420))
        self.assertLess(e[1], a[1]); self.assertLess(abs(e[0] - a[0]), 60)                         # sits just above its anchor

    def test_floating_label_moves_more_than_the_map(self):
        lab = IX.FloatingLabel((600, 500), "Causeway", 0.0, 9.0, depth=0.2)
        def x_of(v): c = ctx(2.0, v); lab.draw(c); return ink_centre(c.ui)[0]
        v1, v2 = View((500, 500), 360, 0, SIZE), View((560, 500), 360, 0, SIZE)
        map_shift = v2.pt((600, 500))[0] - v1.pt((600, 500))[0]; lab_shift = x_of(v2) - x_of(v1)
        self.assertGreater(abs(lab_shift), abs(map_shift))

    def test_image_stamp_says_image_and_event_year_never_does(self):
        st = IX.ImageStamp("Landsat 8, 9 · USGS · July 2022", 0.0, 5.0); ev = IX.EventYear("1959", "causeway was finished", 0.0, 5.0)
        self.assertTrue(("IMAGE · " + st.text).startswith("IMAGE")); self.assertNotIn("IMAGE", ev.words)
        a, b = ctx(2.0), ctx(2.0); st.draw(a); ev.draw(b)
        self.assertLess(ink_centre(a.ui)[0], SIZE[0] / 2); self.assertGreater(ink_centre(b.ui)[0], SIZE[0] / 2)      # never the same place

    def test_punch_is_identity_away_from_hits_and_zooms_at_a_hit(self):
        class Flat:
            size = SIZE; name = "f"; reg = None; start = 0; end = 5
            def render(self, t, **kw):
                a = np.zeros((SIZE[1], SIZE[0], 3), np.uint8); a[:, ::40] = 255; return Image.fromarray(a)
        p = IX.Punch(Flat(), [(2.0, 0.05)]); self.assertEqual(np.asarray(p.render(0.5)).tobytes(), np.asarray(Flat().render(0.5)).tobytes())
        self.assertGreater(p.factor(2.1), 1.03); self.assertNotEqual(np.asarray(p.render(2.1)).tobytes(), np.asarray(Flat().render(2.1)).tobytes())

    def test_parallax_dust_draws_deterministically(self):
        d = IX.ParallaxDust((0, 0, 1000, 1000), 0.0, 5.0, alpha=0.5)
        def run(): c = ctx(2.0, self.view); d.draw(c); return np.asarray(c.ui).tobytes()
        self.assertEqual(run(), run()); self.assertTrue(any(run()))


class TestLiftDimsCaption(unittest.TestCase):
    def test_lifted_word_is_dimmed_not_removed(self):
        ws = semantic.tag_words(words("flows into Gilbert Bay"), {"Gilbert Bay": {}}); cards = C.make_cards(ws); caps = C.WordCaptions(cards, "A")
        w = next(x for x in ws if x["text"] == "Gilbert"); IX.KeywordLift(caps, w["start"], "Gilbert", (0, 0), 0.0, 9.0, label="Gilbert Bay")
        i, j = caps.locate(w["start"], "Gilbert"); self.assertIn((i, j), caps.lifted); self.assertIn((i, j + 1), caps.lifted)
        self.assertAlmostEqual(caps._dim(i, j, w["start"] + 2.0), 0.4, places=2); self.assertEqual(caps._dim(i, 0, w["start"] + 2.0), 1.0)


class TestIntensityAndRoutes(unittest.TestCase):
    def test_long_explanation_is_calm_and_a_revelation_is_energetic(self):
        p = semantic.plan(words("It is not a shoreline: it is a railroad. Almost all of the fresh water flows into the south bay of the lake so the north bay of the lake is always saltier than the rest of it."), {})
        lab = [x["label"] for x in p["intensity"]]; self.assertEqual(lab[0], "energetic"); self.assertEqual(lab[1], "calm")

    def test_a_motion_word_alone_is_not_a_route(self):
        pl = {"Gilbert Bay": {}, "Gunnison Bay": {}}
        self.assertFalse(any(e["kind"] == "route" for e in semantic.plan(words("Water flows into Gilbert Bay, so Gunnison Bay is saltier."), pl)["events"]))
        self.assertTrue(any(e["kind"] == "route" for e in semantic.plan(words("Boats sail from Gilbert Bay to Gunnison Bay."), pl)["events"]))


class TestSfx(unittest.TestCase):
    def test_library_is_deterministic_and_bounded(self):
        for k, f in sfx.LIBRARY.items():
            a, b = f(), f(); self.assertEqual(a.tobytes(), b.tobytes(), k); self.assertLessEqual(float(np.abs(a).max()), 1.0); self.assertEqual(a.shape[1], 2)

    def test_whoosh_is_not_hiss(self):
        a = sfx.whoosh(); p = np.abs(np.fft.rfft(a.mean(1))) ** 2; fr = np.fft.rfftfreq(len(a), 1 / sfx.SR); c = np.cumsum(p) / p.sum()
        self.assertLess(fr[np.searchsorted(c, 0.95)], 8000)

    def test_cue_plan_respects_gap_and_priority(self):
        rep = dict(focus=[dict(kind="impact", t0=5.0, t1=6.5)], decisions=[dict(kind="transition", t=5.05, why="light wipe: x"), dict(kind="callout", t=8.0), dict(kind="event_year", t=8.1)], opening_tilt=True)
        cues = sfx.plan_cues(rep); ts = [c["t"] for c in cues]
        self.assertTrue(all(b - a >= 0.25 - 1e-9 for a, b in zip(ts, ts[1:])))
        self.assertIn("impact", [c["kind"] for c in cues if abs(c["t"] - 5.02) < 0.01]); self.assertIn("rise", [c["kind"] for c in cues])

    def test_mix_keeps_effects_well_under_the_voice(self):
        d = tempfile.mkdtemp(); vp = os.path.join(d, "v.wav"); sr = 22050; t = np.arange(int(3 * sr)) / sr
        v = (0.3 * np.sin(2 * np.pi * 180 * t) * ((t > 0.5) & (t < 2.5))).astype(np.float32)
        with wave.open(vp, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((v * 32767).astype(np.int16).tobytes())
        rep = sfx.mix(vp, [dict(t=1.0, kind="impact"), dict(t=1.5, kind="whoosh")], 3.0, os.path.join(d, "m.wav"), normalise=False)
        self.assertGreaterEqual(rep["margin_db_p5"], 11.0); self.assertIn("CC0", rep["license"])


class TestDirectorEp003Fixes(unittest.TestCase):
    """EP003 render review: a number card unit must not take the next sentence, year ranges are not event years, every picture of a wipe has its own date."""
    def setUp(self):
        import json
        from orbitalatlas.tests import test_visual_v2b as V2B
        base = V2B.TestDirector(); base.setUp(); self.d = d = base.d
        ws = words("Its surface measured 4,209.7 feet. Inflows have fallen 39 percent since 1847. Put the pictures in order, from 1986 to 2022, and it pulls back.", 0.4)
        json.dump(semantic.plan(ws, {}, source="alignment", max_events_per_10s=12), open(f"{d}/story/motion_plan.json", "w"))
        tl = json.load(open(f"{d}/timeline.json")); tl["shots"] = [tl["shots"][0], dict(tl["shots"][2], start=ws[13]["start"])]; tl["end"] = dict(seconds=ws[-1]["end"] + 1.0)
        json.dump(tl, open(f"{d}/timeline.json", "w"))

    def test_unit_stops_at_the_end_of_its_sentence(self):
        from orbitalatlas import director
        prog, rep = director.build(self.d, SIZE, log=lambda m: None, opening_tilt=False)
        nc = [o for o in prog.overlays if type(o).__name__ == "NumberCard"]; self.assertTrue(nc); self.assertEqual(nc[0].unit, "FEET")
        self.assertTrue(all(not t_["problems"] for t_ in rep["texts"]), rep["texts"])
        self.assertTrue(all(not o.unit.endswith("SINCE") for o in nc))

    def test_year_range_is_not_an_event_year_and_a_wipe_dates_both_pictures(self):
        from orbitalatlas import director
        prog, rep = director.build(self.d, SIZE, log=lambda m: None, opening_tilt=False)
        self.assertFalse(any(d["kind"] == "event" and d["year"] in ("1986",) for d in rep["dates"]))
        imgs = [d["asset_label"] for d in rep["dates"] if d["kind"] == "image"]; self.assertIn("July 1986", imgs); self.assertIn("July 2022", imgs)


if __name__ == "__main__":
    unittest.main()
