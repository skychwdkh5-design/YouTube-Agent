#!/usr/bin/env python3
import json, os, sys, tempfile, unittest
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import regrid_nearest as R


class Regrid(unittest.TestCase):
    def mk(self, d, name, px, w, h, x0, ytop, fill=None):
        p = os.path.join(d, name); os.makedirs(p)
        json.dump({"epsg": 32636, "x0": x0, "y_top": ytop, "pixel_m": px, "width": w, "height": h}, open(os.path.join(p, "grid.json"), "w"))
        if fill is not None:
            Image.fromarray(fill).save(os.path.join(p, "y1.png"))
            json.dump({"s1": {"derived_png": "y1.png", "processing": [{"op": "x"}]}}, open(os.path.join(p, "provenance.json"), "w"))
        return p

    def test_coarse_pixels_become_flat_blocks_with_no_new_values(self):
        d = tempfile.mkdtemp()
        src = np.arange(4 * 4 * 3, dtype=np.uint8).reshape(4, 4, 3)
        s = self.mk(d, "src", 30.0, 4, 4, 1000.0, 5000.0, src)
        t = self.mk(d, "tgt", 10.0, 6, 6, 1030.0, 4970.0)
        r = R.regrid(s, t, os.path.join(d, "out"))
        out = np.asarray(Image.open(os.path.join(d, "out", "y1.png")))
        self.assertEqual(out.shape, (6, 6, 3))
        self.assertTrue((out[:3, :3] == src[1, 1]).all())                         # a 3x3 block of target pixels is ONE source pixel
        self.assertEqual({tuple(x) for x in out.reshape(-1, 3)} - {tuple(x) for x in src.reshape(-1, 3)}, set())      # no blended colours
        prov = json.load(open(os.path.join(d, "out", "provenance.json")))
        self.assertIn("NOT an increase of detail", prov["s1"]["processing"][-1]["note"])
        self.assertEqual(r["native_pixel_m"], 30.0)

    def test_uncovered_target_is_refused(self):
        d = tempfile.mkdtemp()
        s = self.mk(d, "src", 30.0, 2, 2, 1000.0, 5000.0, np.zeros((2, 2, 3), np.uint8))
        t = self.mk(d, "tgt", 10.0, 12, 6, 1000.0, 5000.0)
        with self.assertRaises(SystemExit):
            R.regrid(s, t, os.path.join(d, "out"))


if __name__ == "__main__":
    unittest.main()
