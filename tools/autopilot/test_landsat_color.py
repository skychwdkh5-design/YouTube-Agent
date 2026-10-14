#!/usr/bin/env python3
"""Offline tests for landsat_color.py with synthetic Level-1 band files: tone curve, tile mosaic without seams, collar removal, errors."""
import json, math, os, shutil, sys, tempfile, unittest

import numpy as np
from PIL import Image, TiffImagePlugin

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", ".claude", "skills", "yt-geo"))
import geostack as g  # noqa: E402
import landsat_color as lc  # noqa: E402

CENTER = (-112.5, 41.0)
SUN = 60.0


def band_tif(path, arr, x0, y0, epsg=32612, px=30.0):
    ifd = TiffImagePlugin.ImageFileDirectory_v2()
    ifd[33550] = (px, px, 0.0); ifd.tagtype[33550] = 12
    ifd[33922] = (0.0, 0.0, 0.0, float(x0), float(y0), 0.0); ifd.tagtype[33922] = 12
    ifd[34735] = (1, 1, 0, 3, 1024, 0, 1, 1, 1025, 0, 1, 1, 3072, 0, 1, epsg); ifd.tagtype[34735] = 3
    Image.fromarray(arr.astype(np.uint16)).save(path, tiffinfo=ifd)


def mtl(path, sun=SUN, bands=(1, 2, 3, 4), mult=2e-5, add=-0.1, date="2022-07-28"):
    lines = [f"DATE_ACQUIRED = {date}", f"SUN_ELEVATION = {sun}"]
    for b in bands: lines += [f"REFLECTANCE_MULT_BAND_{b} = {mult:.4E}", f"REFLECTANCE_ADD_BAND_{b} = {add}"]
    with open(path, "w") as f: f.write("\n".join(lines))


def dn_for(refl):
    """Digital number that gives this TOA reflectance for the test sun elevation and the OLI scaling."""
    return int(round((refl * math.sin(math.radians(SUN)) + 0.1) / 2e-5))


class Color(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.d = self.tmp.name
        os.makedirs(os.path.join(self.d, "bands"))
        cx, cy = g.lonlat_to_utm(CENTER[0], CENTER[1], 32612)
        self.x0, self.y0 = float(cx) - 9000, float(cy) + 9000           # 600 x 600 px of 30 m around the centre

    def tile(self, name, refl_rgb, rows=(0, 600), collar=0, y_shift=0.0):
        """A tile whose three bands hold a constant reflectance; `rows` selects which 30 m rows exist; `collar` leaves DN=0 pixels at the edge."""
        for b, r in zip((4, 3, 2), refl_rgb):
            a = np.zeros((600, 600), np.uint16)
            a[rows[0]:rows[1]] = dn_for(r)
            if collar: a[:collar] = 0; a[-collar:] = 0; a[:, :collar] = 0; a[:, -collar:] = 0
            band_tif(os.path.join(self.d, "bands", f"{name}_B{b}.TIF"), a, self.x0, self.y0 - y_shift)
        mtl(os.path.join(self.d, "bands", f"{name}_MTL.txt"), bands=(2, 3, 4))

    def spec(self, tiles, aoi=(-112.53, 40.97, -112.47, 41.03), scenes=None):
        s = {"aoi": list(aoi), "pixel_m": 30, "out_dir": "stack", "bands_dir": "bands",
             "scenes": scenes or [{"id": "y", "label": "Y", "tiles": tiles}]}
        p = os.path.join(self.d, "spec.json")
        with open(p, "w") as f: json.dump(s, f)
        return lc.load_spec(p)

    def test_tone_b_matches_the_published_formula(self):
        self.assertAlmostEqual(float(lc.tone_b(np.array([0.02]))[0]), 0.0)
        self.assertAlmostEqual(float(lc.tone_b(np.array([0.60]))[0]), 1.0)
        self.assertAlmostEqual(float(lc.tone_b(np.array([0.31]))[0]), 0.5 ** (1 / 1.8), places=6)
        self.assertEqual(float(lc.tone_b(np.array([-0.3]))[0]), 0.0)

    def test_one_tile_gets_the_curve_per_channel(self):
        self.tile("LC09_L1TP_038031_20220728_X_02_T1", (0.31, 0.20, 0.10))
        r = lc.build(self.spec(["LC09_L1TP_038031_20220728_X_02_T1"]))
        img = np.asarray(Image.open(os.path.join(self.d, "stack", "y.png")))
        want = [int(round(float(lc.tone_b(np.array([x]))[0]) * 255)) for x in (0.31, 0.20, 0.10)]
        self.assertTrue(all(abs(int(img[100, 100, i]) - want[i]) <= 1 for i in range(3)), (img[100, 100], want))
        self.assertTrue(os.path.exists(os.path.join(self.d, "stack", "grid.json")))
        prov = json.load(open(os.path.join(self.d, "stack", "provenance.json")))["y"]
        self.assertEqual(prov["tiles"][0]["bands"], ["B4", "B3", "B2"]); self.assertIn("tone_B", [p["op"] for p in prov["processing"]])

    def test_two_tiles_give_one_seamless_picture_with_no_collar_line(self):
        # north tile has data for the top 400 rows, south tile for the bottom 400 rows: they overlap by 200 rows; both have the same ground reflectance
        self.tile("LC09_L1TP_038031_20220728_N_02_T1", (0.31, 0.20, 0.10), rows=(0, 400), collar=4)
        self.tile("LC09_L1TP_038032_20220728_S_02_T1", (0.31, 0.20, 0.10), rows=(200, 600), collar=4)
        self.spec(["x"])
        spec = self.spec(["LC09_L1TP_038031_20220728_N_02_T1", "LC09_L1TP_038032_20220728_S_02_T1"], aoi=(-112.55, 40.95, -112.45, 41.05))
        lc.build(spec)
        img = np.asarray(Image.open(os.path.join(self.d, "stack", "y.png"))).astype(int)
        spread = img.reshape(-1, 3).max(axis=0) - img.reshape(-1, 3).min(axis=0)
        self.assertLessEqual(int(spread.max()), 1, f"seam or black collar visible: channel spread {spread}")

    def test_the_black_collar_is_never_copied(self):
        self.tile("LC09_L1TP_038031_20220728_N_02_T1", (0.31, 0.20, 0.10), collar=6)
        spec = self.spec(["LC09_L1TP_038031_20220728_N_02_T1"], aoi=(-112.6, 40.9, -112.4, 41.1))
        with self.assertRaises(lc.ColorError) as cm:                       # the AOI reaches into the collar: refused, not filled with black
            lc.build(spec)
        self.assertIn("not fully covered", str(cm.exception))

    def test_a_gap_between_tiles_is_an_error(self):
        self.tile("LC09_L1TP_038031_20220728_N_02_T1", (0.31, 0.20, 0.10), rows=(0, 250))
        self.tile("LC09_L1TP_038032_20220728_S_02_T1", (0.31, 0.20, 0.10), rows=(350, 600))
        with self.assertRaises(lc.ColorError):
            lc.build(self.spec(["LC09_L1TP_038031_20220728_N_02_T1", "LC09_L1TP_038032_20220728_S_02_T1"]))

    def test_different_sun_elevations_still_give_the_same_colour_for_the_same_ground(self):
        # the second tile was taken with a lower sun: its DN is lower for the same reflectance; the MTL sun elevation compensates
        self.tile("LC09_L1TP_038031_20220728_N_02_T1", (0.31, 0.20, 0.10), rows=(0, 400))
        for b, r in zip((4, 3, 2), (0.31, 0.20, 0.10)):
            a = np.zeros((600, 600), np.uint16); a[200:600] = int(round((r * math.sin(math.radians(40.0)) + 0.1) / 2e-5))
            band_tif(os.path.join(self.d, "bands", f"LC09_L1TP_038032_20220728_S_02_T1_B{b}.TIF"), a, self.x0, self.y0)
        mtl(os.path.join(self.d, "bands", "LC09_L1TP_038032_20220728_S_02_T1_MTL.txt"), sun=40.0, bands=(2, 3, 4))
        lc.build(self.spec(["LC09_L1TP_038031_20220728_N_02_T1", "LC09_L1TP_038032_20220728_S_02_T1"], aoi=(-112.52, 40.98, -112.48, 41.02)))
        img = np.asarray(Image.open(os.path.join(self.d, "stack", "y.png"))).astype(int)
        self.assertLessEqual(int((img.reshape(-1, 3).max(0) - img.reshape(-1, 3).min(0)).max()), 1)

    def test_plan_reports_missing_files_and_unsupported_sensors(self):
        r = lc.plan(self.spec(["LC09_L1TP_038031_20220728_N_02_T1", "XX99_L1TP_000000_20000101_X"]))
        self.assertFalse(r["ok"]); self.assertTrue(any("B4.TIF" in m for m in r["missing_files"])); self.assertTrue(any("unsupported" in m for m in r["missing_files"]))

    def test_thematic_mapper_uses_b3_b2_b1(self):
        for b, r in zip((3, 2, 1), (0.31, 0.20, 0.10)):
            band_tif(os.path.join(self.d, "bands", f"LT05_L1TP_038031_19850612_X_02_T1_B{b}.TIF"), np.full((600, 600), dn_for(r), np.uint16), self.x0, self.y0)
        mtl(os.path.join(self.d, "bands", "LT05_L1TP_038031_19850612_X_02_T1_MTL.txt"), bands=(1, 2, 3))
        lc.build(self.spec(["LT05_L1TP_038031_19850612_X_02_T1"]))
        prov = json.load(open(os.path.join(self.d, "stack", "provenance.json")))["y"]
        self.assertEqual(prov["tiles"][0]["bands"], ["B3", "B2", "B1"])


if __name__ == "__main__":
    unittest.main()
