#!/usr/bin/env python3
"""Offline tests for geostack.py and watermask.py - synthetic GeoTIFFs, no network.

    python3 test_geo.py
"""
import io, json, os, shutil, sys, tempfile, unittest
from contextlib import redirect_stdout

import numpy as np
from PIL import Image, TiffImagePlugin

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geostack as g
import watermask as wm


def geotiff(path, arr, x0, y0, epsg=32611, px=30.0):
    """Write a north-up UTM GeoTIFF the way the Landsat browse GeoTIFFs are tagged."""
    ifd = TiffImagePlugin.ImageFileDirectory_v2()
    ifd[33550] = (px, px, 0.0); ifd.tagtype[33550] = 12
    ifd[33922] = (0.0, 0.0, 0.0, float(x0), float(y0), 0.0); ifd.tagtype[33922] = 12
    ifd[34735] = (1, 1, 0, 3, 1024, 0, 1, 1, 1025, 0, 1, 1, 3072, 0, 1, epsg); ifd.tagtype[34735] = 3
    Image.fromarray(arr).save(path, tiffinfo=ifd)


def run(argv, mod=g):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = mod.main(argv)
    return code, json.loads(buf.getvalue())


class UTM(unittest.TestCase):
    def test_central_meridian_and_round_trip(self):
        x, y = g.lonlat_to_utm(-117.0, 36.0, 32611)
        self.assertAlmostEqual(float(x), 500000.0, places=3)
        self.assertAlmostEqual(float(y), 3983948.45, delta=1.0)        # published UTM value
        for lon, lat, epsg in ((-114.737, 36.016, 32611), (18.06, 59.33, 32634), (151.2, -33.86, 32756)):
            x, y = g.lonlat_to_utm(lon, lat, epsg)
            lo, la = g.utm_to_lonlat(x, y, epsg)
            self.assertAlmostEqual(float(lo), lon, places=7); self.assertAlmostEqual(float(la), lat, places=7)

    def test_zone_and_rejects_non_utm(self):
        self.assertEqual(g.epsg_for(-114.5, 36.2), 32611)
        self.assertEqual(g.epsg_for(18.0, 59.3), 32634)
        self.assertEqual(g.epsg_for(151.2, -33.9), 32756)
        with self.assertRaises(g.GeoError):
            g.lonlat_to_utm(0, 0, 4326)


class Stack(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        # a 600x600 scene of 30 m pixels around lon -114.5, lat 36.2, with a marker square
        cx, cy = g.lonlat_to_utm(-114.5, 36.2, 32611)
        self.x0, self.y0 = float(cx) - 9000, float(cy) + 9000
        a = np.full((600, 600, 3), 120, np.uint8)
        a[290:310, 290:310] = (255, 0, 0)                     # marker at the scene centre
        geotiff(os.path.join(self.dir, "a.tif"), a, self.x0, self.y0)
        b = np.full((700, 700, 3), 60, np.uint8)                # second date: shifted origin, same ground
        b[340:360, 340:360] = (0, 0, 255)                      # same ground point, 50 px further in
        geotiff(os.path.join(self.dir, "b.tif"), b, self.x0 - 1500, self.y0 + 1500)

    def spec(self, aoi=(-114.53, 36.17, -114.47, 36.23), **extra):
        s = {"aoi": list(aoi), "pixel_m": 30, "out_dir": "stack",
             "scenes": [{"id": "a", "src": "a.tif", "label": "A", "provenance": {"kind": "test"}},
                        {"id": "b", "src": "b.tif", "label": "B"}]}
        s.update(extra)
        p = os.path.join(self.dir, "stack.json")
        with open(p, "w") as f: json.dump(s, f)
        return p

    def test_dates_align_on_one_grid(self):
        code, d = run([self.spec(), "--confirm", "--contact", "sheet.jpg"])
        self.assertEqual((code, d["status"]), (0, "ok"), d)
        A = np.asarray(Image.open(os.path.join(self.dir, "stack", "a.png")))
        B = np.asarray(Image.open(os.path.join(self.dir, "stack", "b.png")))
        self.assertEqual(A.shape, B.shape)
        ra = np.argwhere(A[..., 0] > 200).mean(axis=0)
        rb = np.argwhere(B[..., 2] > 200).mean(axis=0)
        self.assertLess(np.abs(ra - rb).max(), 1.0)          # the marker lands on the same pixel
        grid = json.load(open(os.path.join(self.dir, "stack", "grid.json")))
        self.assertEqual((grid["epsg"], grid["pixel_m"]), (32611, 30.0))
        prov = json.load(open(os.path.join(self.dir, "stack", "provenance.json")))
        self.assertEqual(prov["a"]["kind"], "test")
        self.assertTrue(os.path.isfile(os.path.join(self.dir, "sheet.jpg")))

    def test_plan_without_confirm_writes_nothing(self):
        code, d = run([self.spec()])
        self.assertEqual((code, d["status"]), (0, "confirm_required"))
        self.assertFalse(os.path.exists(os.path.join(self.dir, "stack")))

    def test_area_outside_a_scene_is_refused(self):
        code, d = run([self.spec(aoi=(-114.7, 36.0, -114.3, 36.4)), "--confirm"])
        self.assertEqual((code, d["status"]), (2, "not_covered"))

    def test_bad_specs(self):
        for extra in ({"scenes": []}, {"pixel_m": 2}, {"scenes": [{"id": "x", "src": "../etc.tif"}]},
                      {"scenes": [{"id": "a", "src": "a.tif"}, {"id": "a", "src": "b.tif"}]}):
            code, d = run([self.spec(**extra), "--confirm"])
            self.assertEqual(code, 2, extra)
        with open(os.path.join(self.dir, "plain.tif"), "wb") as f:
            Image.new("RGB", (10, 10)).save(f, format="TIFF")
        with self.assertRaises(g.GeoError):
            g.read_geotiff(os.path.join(self.dir, "plain.tif"))


class Water(unittest.TestCase):
    def test_mask_keeps_water_and_drops_speckle(self):
        a = np.full((120, 160, 3), (170, 140, 110), np.uint8)    # tan desert
        a[30:90, 40:120] = (20, 30, 50)                        # a lake
        a[5, 5] = (10, 10, 20)                                 # one dark pixel
        a[100:104, 10:14] = (20, 30, 50)                       # a small pond (16 px)
        m = wm.water_mask(a, 75, 5, 50)
        self.assertTrue(m[60, 80]); self.assertFalse(m[5, 5]); self.assertFalse(m[101, 11])
        self.assertEqual(int(m.sum()), 60 * 80 - 4)          # the cross opening trims the 4 corners

    def test_cli(self):
        d = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, d, True)
        a = np.full((50, 50, 3), 160, np.uint8); a[10:40, 10:40] = (15, 25, 45)
        Image.fromarray(a).save(os.path.join(d, "x.png"))
        code, out = run([os.path.join(d, "x.png"), "--out", os.path.join(d, "m.png"), "--min-area-px", "20"], wm)
        self.assertEqual((code, out["water_pixels"]), (0, 896))      # 30x30 minus the 4 opened corners
        self.assertIn("not a survey", out["note"])
        self.assertEqual(run([os.path.join(d, "x.png")], wm)[0], 2)


if __name__ == "__main__":
    unittest.main(verbosity=1)
