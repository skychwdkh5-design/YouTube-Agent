"""EP003 final quality pass: grammatical on-screen phrases (kickers, event-year labels) cut from the narration, traced shoreline
fill/outline layers in the director with a dated legend, and callouts that never point off screen."""
import json, os, tempfile, unittest
import numpy as np
from PIL import Image
from orbitalatlas import fx, layers as L, phrases as PH, text as T
from orbitalatlas.camera import View

SIZE = (640, 360)


class TestPhrases(unittest.TestCase):
    def test_kicker_is_a_whole_clause_not_the_last_nine_words(self):
        s = lambda x: x.split()
        self.assertEqual(" ".join(PH.clause_suffix(s("A 2016 white paper cited by NASA found that the lake's volume has shrunk"))), "the lake's volume has shrunk")
        self.assertEqual(" ".join(PH.clause_suffix(s("The pumps ran from April 1987 to June 1989, and the lake dropped almost"))), "the lake dropped almost")
        self.assertEqual(" ".join(PH.clause_suffix(s("the measurements are plain: in July 2022, the Great Salt Lake measured"))), "in July 2022, the Great Salt Lake measured")
        self.assertEqual(" ".join(PH.clause_suffix(s("In June 1985, its surface measured"))), "In June 1985, its surface measured")
        self.assertEqual(" ".join(PH.clause_suffix(s("Utah State University researchers estimate that inflows have fallen"), 9, max_chars=44)), "inflows have fallen")

    def test_event_label_is_contiguous_and_never_a_lone_preposition(self):
        s = lambda x: x.split()
        self.assertEqual(PH.label(s("At its"), s("high, it covered about 2,300.")), "high")
        self.assertEqual(PH.label([], s("a solid-fill railroad causeway was completed across the middle of the lake.")), "solid-fill railroad causeway")
        self.assertEqual(PH.label(s("NASA lists a new record low"), []), "new record low")
        self.assertEqual(PH.label(s("it peaked in June 1986, and again in March and April of"), []), "March and April")

    def test_lint_flags_the_ep003_defects(self):
        nar = "A 2016 white paper cited by NASA found that the lake's volume has shrunk 48 percent . At its 1986 high".split()
        self.assertTrue(PH.lint("BY NASA FOUND THAT THE LAKE'S VOLUME HAS SHRUNK", nar, standalone=False))
        self.assertTrue(PH.lint("At", nar))
        self.assertTrue(PH.lint("completed across middle lake", "completed across the middle of the lake".split()))
        self.assertEqual(PH.lint("the lake's volume has shrunk", nar, standalone=False), [])


class TestCalloutOffScreen(unittest.TestCase):
    def test_callout_with_an_off_screen_anchor_draws_nothing(self):
        v = View((500, 500), 360, 0, SIZE); c = L.Ctx(SIZE, v, 2.0, T.THEME, T.Registry())
        fx.CalloutPanel((5000, 5000), 0.0, 5.0, "SHORELINE · AUG 1986").draw(c); self.assertFalse(np.asarray(c.ui)[..., 3].any())
        c2 = L.Ctx(SIZE, v, 2.0, T.THEME, T.Registry()); fx.CalloutPanel((500, 500), 0.0, 5.0, "SHORELINE · AUG 1986").draw(c2)
        self.assertTrue(np.asarray(c2.ui)[..., 3].any())


class TestThinOutline(unittest.TestCase):
    def test_thin_outline_is_a_line_not_a_filled_area(self):
        m = np.zeros((400, 400), np.uint8); m[100:300, 100:300] = 255
        v = View((200, 200), 360, 0, SIZE); c = L.Ctx(SIZE, v, 3.0, T.THEME, T.Registry())
        fx.RegionTint(Image.fromarray(m), 0.0, settle_alpha=0.0, flash_peak=0.0, thin=True, glint=False, dur=0.5).draw(c)
        a = np.asarray(c.fills)[..., 3]; cy, cx = [int(x) for x in v.pt((200, 200))[::-1]]
        self.assertTrue(a.any()); self.assertEqual(int(a[cy, cx]), 0)                 # the inside stays clear


class TestDirectorShorelineLayers(unittest.TestCase):
    def test_fill_and_outline_layers_are_drawn_dated_and_reported(self):
        from orbitalatlas.tests import test_visual_v2b as V2B
        from orbitalatlas import director
        base = V2B.TestDirector(); base.setUp(); d = base.d
        g = json.load(open(f"{d}/assets/stack/grid.json")); W, H = g["width"], g["height"]
        a = np.zeros((H // 4, W // 4), np.uint8); a[30:120, 30:120] = 255; b = np.zeros_like(a); b[50:100, 50:100] = 255
        Image.fromarray(a).save(f"{d}/assets/stack/w86.png"); Image.fromarray(b).save(f"{d}/assets/stack/w22.png")
        with open(f"{d}/timeline.json") as fh: tl = json.load(fh)
        tl["assets"]["w86"] = dict(src="assets/stack/w86.png", kind="mask"); tl["assets"]["w22"] = dict(src="assets/stack/w22.png", kind="mask")
        tl["shots"][1]["layers"] += [dict(type="fill", mask="w86", minus="w22", t=[0.3, None]), dict(type="outline", mask="w86", t=[0.5, None], legend="SHORELINE · JUL 1986", at=[-112.5, 41.0])]
        with open(f"{d}/timeline.json", "w") as fh: json.dump(tl, fh)
        prog, rep = director.build(d, SIZE, log=lambda m: None, opening_tilt=False)
        kinds = [x["kind"] for x in rep["decisions"]]; self.assertIn("fill", kinds); self.assertIn("outline", kinds)
        self.assertTrue(any(x["kind"] == "overlay" and "1986" in x["text"] for x in rep["dates"]))
        self.assertTrue(all(not t_["problems"] for t_ in rep["texts"]))


if __name__ == "__main__":
    unittest.main()
