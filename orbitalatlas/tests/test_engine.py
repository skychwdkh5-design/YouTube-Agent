import math, os, sys, unittest
import numpy as np
from PIL import Image, ImageDraw
from orbitalatlas import easing as E, camera as C, layers as L, transitions as TR, sequence as SQ, timing as TM, text as T, synthetic as S, spec as SP

SIZE = (320, 180)


def solid(color, size=SIZE, mark=None):
    im = Image.new("RGB", size, color)
    if mark:
        (x, y), r = mark; ImageDraw.Draw(im).ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255))
    return im


def centroid_white(im):
    a = np.asarray(im).min(axis=2) > 235; ys, xs = np.nonzero(a)
    return (xs.mean(), ys.mean(), a.sum()) if len(xs) else None


class TestEasing(unittest.TestCase):
    def test_endpoints_and_monotone(self):
        for name in ["linear", "smooth", "smoother", "in_cubic", "out_cubic", "in_out_cubic", "in_out_expo", "out_expo", "in_out_quad", "ease"]:
            f = E.get(name); self.assertAlmostEqual(f(0), 0, places=6); self.assertAlmostEqual(f(1), 1, places=6)
            v = [f(i / 50) for i in range(51)]; self.assertTrue(all(b >= a - 1e-9 for a, b in zip(v, v[1:])), name)
    def test_bezier_and_errors(self):
        self.assertAlmostEqual(E.cubic_bezier(0, 0, 1, 1)(0.3), 0.3, places=3)
        with self.assertRaises(ValueError): E.get("nope")
    def test_out_back_overshoots(self): self.assertGreater(max(E.out_back(i / 100) for i in range(101)), 1.0)


class TestCamera(unittest.TestCase):
    def test_roundtrip_with_rotation(self):
        v = C.View((500, 400), 300, 27, (640, 360)); p = np.array([[480.0, 410.0], [520.0, 380.0]])
        np.testing.assert_allclose(v.inv(v.pt(p)), p, atol=1e-6)
        np.testing.assert_allclose(v.pt(v.c), [320, 180], atol=1e-6)
    def test_anchor_lands_at_requested_screen_fraction(self):
        cam = C.Camera([dict(t=0, anchor="a", height=400, rot=15, at=(0.33, 0.4))], (2000, 1200), (640, 360), anchors={"a": (1000, 600)}, clamp=False)
        s = cam.view(0).pt([1000, 600]); np.testing.assert_allclose(s, [0.33 * 640, 0.4 * 360], atol=1e-6)
    def test_clamp_keeps_rotated_window_inside_image(self):
        cam = C.Camera([dict(t=0, center=(10, 10), height=900, rot=30), dict(t=1, center=(1990, 1190), height=900, rot=-30)], (2000, 1200), (640, 360))
        for i in range(21):
            v = cam.view(i / 20); self.assertGreaterEqual(C._Cover((2000, 1200))(v), 0.999)
    def test_check_reports_outside_when_unclamped(self):
        cam = C.Camera([dict(t=0, center=(10, 10), height=900)], (2000, 1200), (640, 360), clamp=False)
        self.assertTrue(any(i[0] == "window_outside_image" for i in cam.check(tmax=0.2)))
    def test_spline_velocity_continuous_and_eased_rests(self):
        keys = [dict(t=0, center=(500, 600), height=400), dict(t=1, center=(1000, 600), height=400), dict(t=2, center=(1500, 600), height=400)]
        sp = C.Camera(keys, (2000, 1200), (640, 360), mode="spline"); ea = C.Camera(keys, (2000, 1200), (640, 360), mode="eased")
        self.assertGreater(sp.speed(1.0), 1.0); self.assertLess(ea.speed(1.0), 0.5)          # eased rests at the key, spline flows through it
        x = [sp.view(i / 100).c[0] for i in range(201)]; d = np.diff(x); self.assertLess(np.abs(np.diff(d)).max(), 0.5 * np.abs(d).max())
    def test_track_follows_with_lag(self):
        cam = C.Camera([dict(t=0, center=(500, 500), height=600)], (2000, 1200), (640, 360), track=(lambda t: (500 + 100 * t, 600), 0.5))
        np.testing.assert_allclose(cam.view(2.0).c, [650, 600], atol=1e-6)
    def test_fit_keeps_points_in_safe_frame(self):
        pts = [(100, 100), (900, 300), (500, 700)]; c, h = C.fit(pts, (640, 360), margin=0.1, rot=20)
        v = C.View(c, h, 20, (640, 360)); s = v.pt(pts)
        self.assertTrue((s[:, 0] >= 63).all() and (s[:, 0] <= 577).all() and (s[:, 1] >= 35).all() and (s[:, 1] <= 325).all())
    def test_render_matches_view_geometry(self):
        img = Image.new("RGB", (1000, 600), (0, 0, 0)); ImageDraw.Draw(img).ellipse([480, 280, 520, 320], fill=(255, 255, 255))
        v = C.View((500, 300), 300, 40, SIZE); out = C.Pyramid(img).render(v); cx, cy, n = centroid_white(out)
        np.testing.assert_allclose([cx, cy], v.pt([500, 300]), atol=1.0)


class TestLayersAndSpec(unittest.TestCase):
    def test_overlay_is_anchored_to_source_pixels(self):
        img, meta = S.islands((1200, 675), 3)
        keys = [dict(t=0, center=(600, 337), height=600), dict(t=2, center=(700, 380), height=300, rot=10)]
        on = L.Scene(img, keys, size=SIZE, overlays=[L.PulseMarker((700, 380), 0.0, color=(255, 0, 255), r=90)]); off = L.Scene(img, keys, size=SIZE)
        for t in (1.0, 2.0):
            d = np.abs(np.asarray(on.render(t, blur=False), int) - np.asarray(off.render(t, blur=False), int)).sum(axis=2)
            want = on.camera.view(t).pt([700, 380]); ys, xs = np.nonzero(d > 12); self.assertGreater(len(xs), 8)
            self.assertLess(abs(xs.mean() - want[0]), 8); self.assertLess(abs(ys.mean() - want[1]), 8)       # change is centred on the anchor
    def test_registry_collision_and_outside(self):
        r = T.Registry(); r.add("a", (10, 10, 100, 40)); r.add("b", (50, 20, 150, 60)); r.add("c", (300, 10, 400, 40))
        self.assertEqual(r.collisions(), [("a", "b")]); self.assertEqual(r.outside((320, 180), margin=0), ["c"])
    def test_blend_modes(self):
        base = Image.new("RGB", (4, 4), (100, 100, 100)); top = Image.new("RGBA", (4, 4), (100, 100, 100, 255))
        self.assertEqual(L.blend(base, top, "add").getpixel((0, 0)), (200, 200, 200)); self.assertEqual(L.blend(base, top, "normal", 0.5).getpixel((0, 0)), (100, 100, 100))
    def test_spec_builds_two_different_scenes_with_one_code_path(self):
        import json
        with open(os.path.join(os.path.dirname(SP.__file__), "demo", "demo_specs.json")) as fh: specs = json.load(fh)
        for k in ("islands_wide", "city_river"):
            specs[k]["image"]["size"] = [1200, 675]
        a = SP.scene_from_spec(specs["islands_wide"], SIZE); b = SP.scene_from_spec(specs["city_river"], SIZE)
        self.assertNotEqual(a.pyr.size, (0, 0)); self.assertEqual(type(a), type(b))
        for sc in (a, b):
            f = sc.render(sc.end); self.assertEqual(f.size, SIZE)
        self.assertIn("TRACED", [m["cls"] for m in a.manifest()])
    def test_missing_asset_detected(self):
        self.assertEqual(SP.check_assets({"image": {"path": "/nonexistent/x.jpg"}}), ["/nonexistent/x.jpg"])
        with self.assertRaises(FileNotFoundError): SP.load_image({"path": "/nonexistent/x.jpg"})
    def test_cues_from_words(self):
        words = [dict(text="So", start=1.0, end=1.2), dict(text="how", start=1.2, end=1.4), dict(text="Dubai,", start=2.0, end=2.4)]
        c = TM.Cues.from_words(words, offset=0.5); self.assertAlmostEqual(c.start("dubai"), 1.5); self.assertTrue(c.frame_accurate)
        self.assertFalse(TM.Cues.from_words(words, source="estimated").frame_accurate)
        with self.assertRaises(KeyError): c.start("nowhere")


class TestTransitions(unittest.TestCase):
    A = solid((200, 60, 60), mark=((100, 90), 20)); B = solid((60, 60, 200), mark=((220, 90), 20))
    def all_transitions(self):
        return [TR.Dissolve(0.5), TR.Push("left", duration=0.6), TR.Push("up", a_rate=0.5, duration=0.6), TR.WhipPan("right"), TR.CinematicPush((0.4, 0.5)), TR.MaskReveal("linear", angle=0),
                TR.MaskReveal("radial", center=(0.5, 0.5), edge_color=(255, 255, 0)), TR.MaskReveal("map", tmap=np.tile(np.linspace(0, 1, 64), (36, 1))),
                TR.GeoFocus((0.5, 0.5)), TR.ScaleMatch((0.3, 0.5), (0.7, 0.5), 0.2, 0.2), TR.DateTransition("2006", "2022"), TR.DateTransition("2006", "2022", mode="dissolve")]
    def test_endpoints_are_the_inputs(self):
        for t in self.all_transitions():
            self.assertEqual(t(self.A, self.B, 0.0).tobytes()[:150], self.A.tobytes()[:150], t.name)
            self.assertEqual(t(self.A, self.B, 1.0).tobytes()[:150], self.B.tobytes()[:150], t.name)
    def test_midframes_are_real_composites_without_black_or_nan(self):
        for t in self.all_transitions():
            for u in (0.25, 0.5, 0.75):
                f = t(self.A, self.B, u); a = np.asarray(f, np.float32); self.assertEqual(f.size, SIZE, t.name)
                self.assertGreater(a.mean(), 25, f"{t.name} u={u} too dark"); self.assertFalse(np.array_equal(np.asarray(f), np.asarray(self.A)), t.name); self.assertFalse(np.array_equal(np.asarray(f), np.asarray(self.B)), t.name)
    def test_every_frame_changes_during_transition(self):
        for t in self.all_transitions():
            prev = None; changed = 0; n = 12
            for i in range(1, n):
                f = np.asarray(t(self.A, self.B, i / n), np.float32)
                if prev is not None and np.abs(f - prev).mean() > 0.05: changed += 1
                prev = f
            self.assertGreaterEqual(changed, n - 4, f"{t.name} stalls ({changed}/{n-2})")
    def test_easing_is_configurable(self):
        lin = TR.MaskReveal("linear", ease="linear", feather=0.01); cub = TR.MaskReveal("linear", ease="in_cubic", feather=0.01)
        r = lambda t: (np.asarray(t(self.A, self.B, 0.5), np.float32)[:, :, 2] > 150).mean()
        self.assertGreater(r(lin), r(cub) + 0.2)
    def test_push_geometry(self):
        f = np.asarray(TR.Push("left", ease="linear")(self.A, self.B, 0.5)); np.testing.assert_array_equal(f[:, :160], np.asarray(self.A)[:, 160:]); np.testing.assert_array_equal(f[:, 160:], np.asarray(self.B)[:, :160])
    def test_shutter_blur_smooths_edges(self):
        sharp = np.asarray(TR.Push("left", ease="linear")(self.A, self.B, 0.5), np.float32); soft = np.asarray(TR.Push("left", ease="linear", shutter=0.1, samples=12)(self.A, self.B, 0.5), np.float32)
        self.assertGreater(len(np.unique(soft[90, :, 2])), len(np.unique(sharp[90, :, 2])))
    def test_scale_match_lands_subject_on_subject(self):
        W, H = 640, 360; a = solid((30, 30, 30), (W, H), mark=((200, 180), 30)); b = solid((20, 80, 20), (W, H), mark=((440, 180), 60))
        t = TR.ScaleMatch((200 / W, 0.5), (440 / W, 0.5), 60 / H, 120 / H)
        pe, se = t.match_error((W, H)); self.assertLess(pe, 1e-6); self.assertLess(se, 1e-6)
        s, pa, q = t.a_transform((W, H), 1.0); end = warp_a = TR.warp(a, s, pa, q); cx, cy, n = centroid_white(end)
        self.assertLess(abs(cx - 440), 1.5); self.assertLess(abs(math.sqrt(n / math.pi) - 60), 3)
    def test_from_spec(self):
        t = TR.from_spec({"type": "push", "direction": "up", "duration": 0.7}); self.assertEqual((t.name, t.duration), ("push", 0.7))
        with self.assertRaises(ValueError): TR.from_spec({"type": "nope"})
    def test_date_transition_draws_digits(self):
        f = np.asarray(TR.DateTransition("2006", "2022", mode="dissolve")(self.A, self.B, 0.5), np.int32); g = np.asarray(Image.blend(self.A, self.B, E.smoother(0.5)), np.int32)
        self.assertGreater(np.abs(f - g).sum(), 5000)


class TestSequence(unittest.TestCase):
    def make(self, d_tr=0.5):
        img, _ = S.islands((900, 506), 3)
        mk = lambda x: L.Scene(img, [dict(t=0, center=(x, 250), height=400), dict(t=2, center=(x + 100, 250), height=300)], size=SIZE)
        return SQ.Sequence([SQ.Shot(mk(300), 2.0), SQ.Shot(mk(500), 2.0), SQ.Shot(mk(400), 2.0)], [TR.Push("left", duration=d_tr), TR.Dissolve(d_tr)])
    def test_schedule_and_duration(self):
        s = self.make(); self.assertAlmostEqual(s.duration, 6.0 - 1.0); sc = s.schedule()
        self.assertAlmostEqual(sc["transitions"][0]["t0"], 1.5); self.assertAlmostEqual(sc["transitions"][0]["t1"], 2.0); self.assertAlmostEqual(sc["transitions"][1]["t0"], 3.0); self.assertAlmostEqual(sc["transitions"][1]["t1"], 3.5)
    def test_render_outside_and_inside_windows(self):
        s = self.make(); a = s.render(0.5); b = s.render(1.75); self.assertEqual(a.size, SIZE); self.assertFalse(np.array_equal(np.asarray(a), np.asarray(b)))
        np.testing.assert_array_equal(np.asarray(s.render(1.0)), np.asarray(s.shots[0].scene.render(1.0)))
    def test_overlong_transition_is_reported(self):
        s = self.make(d_tr=2.5); self.assertTrue(s.problems)


class TestBackwardCompatibility(unittest.TestCase):
    def test_dubai_engine_still_imports_and_runs(self):
        eng = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "productions", "dubai", "motion", "engine")
        if not os.path.isdir(eng): self.skipTest("dubai engine not present")
        sys.path.insert(0, eng)
        try:
            import motionlib as ML
            self.assertAlmostEqual(ML.smoother(0.5), 0.5)
            cam = ML.SplineCam([(0, 500, 300, 400), (2, 900, 400, 300)], (2000, 1200)); v = cam.view(1.0); self.assertEqual(v.k, 1920 / v.crop[2])
        finally:
            sys.path.remove(eng)


if __name__ == "__main__":
    unittest.main()
