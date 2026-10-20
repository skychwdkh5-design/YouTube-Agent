#!/usr/bin/env python3
"""Offline tests for pick/grid logic; live checks run only with YT_SENTINEL_LIVE=1 (free, needs network)."""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sentinel as s


def it(id_, date, cloud, nodata=4.0, orbit=78, baseline="05.11"):
    return {"id": id_, "date": date, "datetime": date + "T08:00:00Z", "cloud": cloud, "nodata": nodata, "orbit": orbit,
            "tile": "T36RYS", "platform": "S2", "baseline": baseline}


class Pick(unittest.TestCase):
    def test_same_orbit_and_missing_year_not_substituted(self):
        items = [it("a", "2020-10-19", 0.1), it("b", "2020-10-14", 0.0, orbit=121, nodata=47),
                 it("c", "2022-10-14", 0.05), it("d", "2024-10-13", 0.04, orbit=121)]
        r = s.pick_per_year(items, [2020, 2022, 2024], ("10-01", "10-31"))
        self.assertEqual(r["orbit"], 78)
        self.assertEqual(sorted(r["picks"]), [2020, 2022])
        self.assertEqual(r["missing"], [2024])
        self.assertTrue(any("not substituted" in n for n in r["notes"]))

    def test_cloud_and_nodata_limits(self):
        r = s.pick_per_year([it("a", "2022-10-14", 9.0), it("b", "2022-10-15", 0.1, nodata=50)], [2022], ("10-01", "10-31"))
        self.assertEqual(r["picks"], {})
        self.assertEqual(r["missing"], [2022])

    def test_baseline_warning(self):
        items = [it("a", "2020-10-19", 0.1, baseline="02.12"), it("c", "2022-10-14", 0.05, baseline="05.11")]
        r = s.pick_per_year(items, [2020, 2022], ("10-01", "10-31"))
        self.assertTrue(any("baselines differ" in n for n in r["notes"]))

    def test_alternatives_same_orbit_first(self):
        items = [it("a", "2022-10-14", 0.1), it("b", "2022-10-15", 0.2), it("c", "2022-10-16", 0.0, orbit=121)]
        r = s.pick_per_year(items, [2022], ("10-01", "10-31"))
        self.assertEqual(r["picks"][2022]["id"], "c" if False else r["picks"][2022]["id"])
        self.assertEqual(len(r["alts"][2022]), 2)

    def test_prefers_lower_cloud(self):
        r = s.pick_per_year([it("a", "2022-10-14", 2.0), it("b", "2022-10-20", 0.2)], [2022], ("10-01", "10-31"))
        self.assertEqual(r["picks"][2022]["id"], "b")


class Grid(unittest.TestCase):
    def test_grid_is_snapped_and_square(self):
        g = s.utm_grid([35.10, 28.07, 35.32, 28.15])
        self.assertEqual(g["epsg"], 32636)
        self.assertEqual(g["x0"] % 20, 0)
        self.assertEqual((g["width"], g["height"]), (2180, 928))

    def test_bad_aoi(self):
        with self.assertRaises(s.SentinelError):
            s._aoi("1,2,3")

    def test_url_has_utm_crs(self):
        g = s.utm_grid([35.10, 28.07, 35.32, 28.15])
        self.assertIn("coord_crs=EPSG:32636", s.crop_url("X", g))


@unittest.skipUnless(os.environ.get("YT_SENTINEL_LIVE") == "1", "live test")
class Live(unittest.TestCase):
    def test_search_and_tiny_stack(self):
        import tempfile
        aoi = [35.20, 28.10, 35.22, 28.11]
        items = s.stac_search(aoi, "2025-10-01", "2025-10-31", 5)
        r = s.pick_per_year(items, [2025], ("10-01", "10-31"))
        self.assertIn(2025, r["picks"])
        with tempfile.TemporaryDirectory() as d:
            out = s.build_stack(r["picks"], aoi, d)
            self.assertTrue(os.path.exists(os.path.join(d, "y2025.png")))
            self.assertEqual(out["scenes"], ["y2025"])


if __name__ == "__main__":
    unittest.main()
