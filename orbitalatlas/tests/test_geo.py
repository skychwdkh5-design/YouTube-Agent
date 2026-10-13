import math, os, unittest
import numpy as np
from orbitalatlas import geo as G

DATA = os.environ.get("ORBITALATLAS_GEODATA", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "natural_earth"))
HAVE = os.path.exists(os.path.join(DATA, "ne_10m_land.geojson"))


class TestProjection(unittest.TestCase):
    def test_roundtrip_and_centre(self):
        v = G.GlobeView(55.0, 25.0, 700, 30, (640, 360))
        x, y, vis = v.pt(np.array([55.0, 56.0]), np.array([25.0, 26.0]))
        self.assertTrue(vis.all()); self.assertAlmostEqual(x[0], 320, places=6); self.assertAlmostEqual(y[0], 180, places=6)
        lon, lat, ok, z = v.inv(x[None, :], y[None, :]); np.testing.assert_allclose(lon[0], [55, 56], atol=1e-6); np.testing.assert_allclose(lat[0], [25, 26], atol=1e-6)
    def test_far_side_is_hidden(self):
        v = G.GlobeView(0, 0, 14000, 0, (640, 360)); _, _, vis = v.pt(np.array([0.0, 180.0, 95.0]), np.array([0.0, 0.0, 0.0])); self.assertEqual(list(vis), [True, False, False])
    def test_scale_matches_great_circle_distance_near_centre(self):
        v = G.GlobeView(55.0, 25.0, 700, 0, (1920, 1080)); x, y, _ = v.pt(np.array([55.0, 55.5]), np.array([25.0, 25.0]))
        km = G.haversine_km(55.0, 25.0, 55.5, 25.0); self.assertAlmostEqual(abs(x[1] - x[0]) * v.km_per_px, km, delta=km * 0.002)
    def test_bearing_rotates_north_off_vertical(self):
        v0 = G.GlobeView(55, 25, 700, 0, (640, 360)); v90 = G.GlobeView(55, 25, 700, 90, (640, 360))
        _, y0, _ = v0.pt(np.array([55.0]), np.array([26.0])); x90, y90, _ = v90.pt(np.array([55.0]), np.array([26.0]))
        self.assertLess(y0[0], 180); self.assertLess(abs(y90[0] - 180), 0.5); self.assertNotAlmostEqual(x90[0], 320, places=1)
    def test_haversine_known_distance(self):
        self.assertAlmostEqual(float(G.haversine_km(0, 0, 0, 1)), 111.19, delta=0.2)           # one degree of latitude
        a = (55.2869, 25.2149, 54.3666, 24.4667)                                                 # Dubai, Abu Dhabi (Natural Earth place points)
        p1, p2, dl = math.radians(a[1]), math.radians(a[3]), math.radians(a[2] - a[0])
        cosine_law = 6371.0088 * math.acos(math.sin(p1) * math.sin(p2) + math.cos(p1) * math.cos(p2) * math.cos(dl))   # independent formula
        self.assertAlmostEqual(float(G.haversine_km(*a)), cosine_law, delta=0.05); self.assertTrue(110 < cosine_law < 135)


class TestGeoCamera(unittest.TestCase):
    def cam(self, **kw): return G.GeoCamera([dict(t=0, lon=20, lat=10, span_km=14000), dict(t=2, lon=55, lat=25, span_km=700), dict(t=4, lon=55.1, lat=25.2, span_km=180)], (640, 360), **kw)
    def test_endpoints_and_great_circle_midpoint(self):
        c = self.cam(); v0, v2 = c.view(0), c.view(2); self.assertAlmostEqual(v0.lon, 20); self.assertAlmostEqual(v2.lat, 25, places=6)
        m = G.GeoCamera([dict(t=0, lon=0, lat=0, span_km=5000), dict(t=1, lon=90, lat=0, span_km=5000, ease="linear")], (640, 360)).view(0.5); self.assertAlmostEqual(m.lon, 45, places=3)
    def test_span_log_interpolation_and_monotone_zoom(self):
        c = self.cam(); spans = [c.view(t).span for t in np.linspace(0, 4, 81)]; self.assertTrue(all(b <= a + 1e-6 for a, b in zip(spans, spans[1:])))
    def test_no_jumps(self):
        c = self.cam(); prev = c.view(0)
        for t in np.linspace(0.05, 4, 80):
            v = c.view(t); self.assertLess(float(G.haversine_km(prev.lon, prev.lat, v.lon, v.lat)), 900); prev = v
    def test_check_flags_span_and_hidden_anchor(self):
        c = G.GeoCamera([dict(t=0, lon=0, lat=0, span_km=5000), dict(t=1, lon=0, lat=0, span_km=5)], (640, 360), anchors={"far": (170.0, 0.0)})
        r = [i[0] for i in c.check(must_show={"far": (0, 1)})]; self.assertIn("span_out_of_range", r); self.assertIn("anchor_outside_safe_frame", r)
    def test_spline_mode_has_continuous_path(self):
        c = G.GeoCamera([dict(t=0, lon=10, lat=10, span_km=9000), dict(t=1, lon=30, lat=20, span_km=3000), dict(t=2, lon=50, lat=25, span_km=1000), dict(t=3, lon=55, lat=25, span_km=300)], (640, 360), mode="spline")
        lons = [c.view(t).lon for t in np.linspace(0, 3, 61)]; d = np.diff(lons); self.assertLess(np.abs(np.diff(d)).max(), 0.6 * np.abs(d).max() + 1e-9)


class TestPolylines(unittest.TestCase):
    def test_visible_runs_split_at_horizon(self):
        v = G.GlobeView(0, 0, 14000, 0, (640, 360)); lon = np.linspace(-170, 170, 400); x, y, vis = v.pt(lon, np.zeros_like(lon))
        runs = G.visible_runs(x, y, vis, 640, 360); self.assertEqual(len(runs), 1); self.assertTrue(all(len(r) > 2 for r in runs))


@unittest.skipUnless(HAVE, "Natural Earth data not fetched (tools/fetch_natural_earth.sh)")
class TestRealData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gd = G.GeoData(DATA); land = cls.gd.land("10m"); cls.ras = G.GeoRaster().add(land, (30, 8, 72, 42), 0.01)
    def cover(self, lon, lat): return float(self.ras.sample(np.array([lon]), np.array([lat]))[0])
    def test_known_places_are_on_the_right_side_of_the_coast(self):
        self.assertGreater(self.cover(46.72, 24.63), 0.9)       # Riyadh (inland)
        self.assertLess(self.cover(51.5, 27.0), 0.1)            # open water in the Persian Gulf
        self.assertLess(self.cover(60.0, 20.0), 0.1)            # Arabian Sea
        self.assertGreater(self.cover(55.0, 22.5), 0.9)         # Rub' al Khali, inside the UAE/Saudi desert
    def test_dubai_is_inside_the_uae_polygon_and_near_the_coast(self):
        uae = self.gd.country("United Arab Emirates"); r = G.GeoRaster().add(uae, (51, 22, 57.6, 26.9), 0.0025)
        lon, lat = self.gd.place("Dubai", "United Arab Emirates"); self.assertGreater(float(r.sample(np.array([lon]), np.array([lat]))[0]), 0.9)
        self.assertLess(float(r.sample(np.array([51.5]), np.array([27.0]))[0]), 0.05)
        self.assertAlmostEqual(lon, 55.29, delta=0.05); self.assertAlmostEqual(lat, 25.21, delta=0.05)
    def test_label_anchors_come_from_the_data(self):
        gulf = G.polygon_centroid(G._polys(self.gd.feature("ne_10m_geography_marine_polys", "name", "Persian Gulf")["geometry"]))
        self.assertTrue(48 < gulf[0] < 56 and 24 < gulf[1] < 30); self.assertLess(self.cover(*gulf), 0.1)         # centroid lies in water
    def test_uae_ring_is_closed_and_inside_bbox(self):
        main = max(self.gd.country("United Arab Emirates"), key=lambda p: len(p[0])); r = np.array(main[0]); np.testing.assert_allclose(r[0], r[-1])
        self.assertTrue((r[:, 0] > 51).all() and (r[:, 0] < 57).all() and (r[:, 1] > 22).all() and (r[:, 1] < 26.5).all())


if __name__ == "__main__":
    unittest.main()
