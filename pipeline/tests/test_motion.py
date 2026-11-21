import importlib.util, os, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
HAVE = all(importlib.util.find_spec(m) for m in ("numpy", "PIL"))


@unittest.skipUnless(HAVE, "needs numpy + Pillow")
class MotionPass(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import motion
        cls.m = motion

    def tl(self):
        sh = [{"id": "cover", "start": 0, "layers": [{"type": "graphic", "asset": "cover"}]},
              {"id": "a", "start": 0.0333, "layers": [{"type": "video", "asset": "a"}]},
              {"id": "b", "start": 4.0, "layers": [{"type": "video", "asset": "b"}]},
              {"id": "c", "start": 8.0, "layers": [{"type": "video", "asset": "a"}]},
              {"id": "d", "start": 12.0, "layers": [{"type": "video", "asset": "b"}]}]
        return {"shots": sh, "assets": {"a": {"src": "a.mp4"}, "b": {"src": "b.mp4"}}}

    def test_cover_is_not_a_cut_and_kinds_vary(self):
        c = self.m.cuts(self.tl(), {})
        self.assertEqual([x["t"] for x in c], [4.0, 8.0, 12.0])
        self.assertEqual(len({x["kind"] for x in c}), 3)

    def test_override_and_unknown_kind(self):
        self.assertEqual(self.m.cuts(self.tl(), {"transitions": {"c": "none"}})[1]["kind"], "none")
        with self.assertRaises(SystemExit):
            self.m.cuts(self.tl(), {"transitions": {"c": "spin"}})

    def test_transition_keeps_size_and_fades_out(self):
        from PIL import Image
        img = Image.new("RGB", (self.m.W, self.m.H), (40, 80, 120))
        for kind in ("whip_l", "whip_r", "zoom", "flash", "glitch"):
            cut = {"t": 4.0, "kind": kind}
            self.assertEqual(self.m.transition(img, 4.0, cut, 1).size, img.size)
            self.assertIs(self.m.transition(img, 4.0 + self.m.WIN + 0.01, cut, 1), img)

    def test_hero_phrase_lookup(self):
        words = [{"text": "since", "start": 1.0, "end": 1.2}, {"text": "1972.", "start": 1.3, "end": 2.0}]
        self.assertAlmostEqual(self.m.find_phrase(words, "since 1972"), 1.0)
        with self.assertRaises(SystemExit):
            self.m.find_phrase(words, "since 1980")

    def test_source_line_names_place(self):
        tl = self.tl()
        rights = {"assets": [{"src": "a.mp4", "credit": "NASA Operation IceBridge footage, Alaska", "footage": "live"}]}
        line = self.m.source_line(tl, rights, {}, tl["shots"][1])
        self.assertIn("ALASKA", line)
        self.assertTrue(line.startswith("ARCHIVE"))


if __name__ == "__main__":
    unittest.main()
