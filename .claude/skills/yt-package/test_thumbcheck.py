import os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw
import thumbcheck as T


class TC(unittest.TestCase):
    def img(self, bg, name):
        im = Image.new("RGB", (1280, 720), bg)
        d = ImageDraw.Draw(im)
        d.rectangle((60, 500, 1100, 680), fill=(255, 255, 255)); d.rectangle((60, 60, 700, 200), fill=(255, 210, 30))
        p = os.path.join(tempfile.mkdtemp(), name); im.save(p); return p

    def test_gray_low_contrast_fails_and_dark_saturated_passes(self):
        gray = Image.new("RGB", (1280, 720), (150, 150, 150)); p = os.path.join(tempfile.mkdtemp(), "g.png"); gray.save(p)
        self.assertEqual(T.main([p]), 1)
        self.assertEqual(T.main([self.img((10, 20, 60), "ok.png")]), 0)

    def test_wrong_size_fails(self):
        p = os.path.join(tempfile.mkdtemp(), "s.png"); Image.new("RGB", (640, 360), (10, 20, 60)).save(p)
        self.assertEqual(T.main([p]), 1)


if __name__ == "__main__":
    unittest.main()


class Calibration(unittest.TestCase):
    def test_published_references_pass_everything_but_size(self):
        ref = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "assets", "thumbnail-reference")
        names = sorted(os.listdir(ref)); self.assertEqual(len(names), 4)
        for n in names:
            r = T.check(T.metrics(os.path.join(ref, n))); r.pop("is_1280x720")
            self.assertTrue(all(r.values()), (n, r))
