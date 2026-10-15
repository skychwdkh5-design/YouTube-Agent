"""illustrate: radar line-of-sight geometry, drawing primitives, the S3 diagram (labels, collisions, determinism) and the evidence placeholder."""
import math, unittest
import numpy as np
from PIL import Image, ImageDraw
from orbitalatlas import illustrate as I, sequence as S, transitions as TR, textrec

SMALL = (480, 270)


class TestGeometry(unittest.TestCase):
    def test_vertical_drop_seen_from_above_is_fully_seen(self):
        g = I.los_change((500, -1e6), (500, 0), (0, 10)); self.assertAlmostEqual(g["ratio"], 1.0, places=4); self.assertAlmostEqual(g["delta"], 10.0, places=3)

    def test_oblique_view_sees_cos_incidence_of_the_drop(self):
        sat, pt = (420, 200), (880, 700); g = I.los_change(sat, pt, (0, 110))
        self.assertAlmostEqual(g["ratio"], math.cos(math.radians(g["incidence_deg"])), places=6)
        self.assertLess(g["los_component"], g["vertical"]); self.assertGreater(g["los_component"], 0)

    def test_range_change_matches_projection_for_a_far_satellite(self):
        g = I.los_change((0, -5e5), (3e5, 0), (0, 5)); self.assertAlmostEqual(g["delta"], g["los_component"], places=2)

    def test_a_grazing_view_sees_almost_nothing_of_a_vertical_drop(self):
        g = I.los_change((-1e6, -10), (0, 0), (0, 10)); self.assertLess(g["ratio"], 0.001)

    def test_upward_motion_is_negative(self):
        self.assertLess(I.los_change((420, 200), (880, 700), (0, -50))["delta"], 0)

    def test_foot_lies_on_the_line_of_sight_and_the_residual_is_perpendicular(self):
        sat, pt, d = np.array((420., 200.)), np.array((880., 700.)), np.array((0., 110.)); g = I.los_change(sat, pt, d); F = np.array(g["foot"]); u = (pt - sat) / np.linalg.norm(pt - sat)
        self.assertAlmostEqual(float((F - sat)[0] * u[1] - (F - sat)[1] * u[0]), 0.0, places=6)                    # F on the line through the satellite and the point
        self.assertAlmostEqual(float((pt + d - F) @ u), 0.0, places=6)                         # residual is perpendicular to the line of sight

    def test_incidence_zero_when_overhead(self): self.assertAlmostEqual(I.incidence_deg((10, -100), (10, 0)), 0.0, places=6)

    def test_bowl_is_deepest_at_its_centre_and_flat_far_away(self):
        self.assertAlmostEqual(float(I.bowl_surface(500, 700, 500, 80, 200)), 780.0); self.assertAlmostEqual(float(I.bowl_surface(5000, 700, 500, 80, 200)), 700.0, places=3)


class TestPrimitives(unittest.TestCase):
    def test_dashed_draws_only_the_requested_part(self):
        def ink(upto):
            im = Image.new("RGBA", (200, 40), (0, 0, 0, 0)); I.dashed(ImageDraw.Draw(im), (0, 20), (199, 20), (255, 255, 255), 2, 6, 4, scale=1, upto=upto); return int((np.asarray(im)[..., 3] > 0).sum())
        self.assertEqual(ink(0.0), 0); self.assertGreater(ink(1.0), ink(0.5)); self.assertGreater(ink(0.5), 0)

    def test_arc_points_lie_on_the_circle(self):
        p = I.arc_points((10, 20), 50, -30, 30); self.assertTrue(np.allclose(np.hypot(p[:, 0] - 10, p[:, 1] - 20), 50))

    def test_wave_phase_shifts_the_crest(self):
        a, b = I.wave(0, 400, 0, 10, 100, 0.0), I.wave(0, 400, 0, 10, 100, math.pi); self.assertTrue(np.allclose(a[:, 1], -b[:, 1], atol=1e-6))


class TestRadarDiagram(unittest.TestCase):
    def setUp(self): self.d = I.RadarGeometryDiagram(SMALL, 12.0)

    def test_frame_size_and_determinism(self):
        a, b = self.d.render(6.1), self.d.render(6.1); self.assertEqual(a.size, SMALL); self.assertEqual(a.tobytes(), b.tobytes())

    def test_it_changes_over_time(self):
        f = [np.asarray(self.d.render(t), np.int16) for t in (0.3, 2.0, 5.5, 8.0, 10.0)]
        for x, y in zip(f, f[1:]): self.assertGreater(float(np.abs(x - y).mean()), 0.5)

    def test_the_pulse_target_is_where_the_ground_ends_up(self):
        d = self.d; end = float(d._surface(d.pt[0], 11.0)); self.assertAlmostEqual(end, d.pt[1] + d.drop, places=6)

    def test_timeline_windows_are_ordered_and_inside_the_shot(self):
        for k, (a, b) in self.d.tl.items(): self.assertTrue(0 <= a < b <= self.d.duration, k)
        self.assertLessEqual(self.d.tl["pulse1"][1], self.d.tl["echo1"][1]); self.assertLess(self.d.tl["sink"][1], self.d.tl["pulse2"][0] + 0.3)

    def test_captions_never_overlap_in_time(self):
        c = sorted(self.d.captions)
        for a, b in zip(c, c[1:]): self.assertLessEqual(a[1], b[0] + 0.3)

    def test_no_text_collides_or_leaves_the_title_safe_frame_at_any_time(self):
        bad = []
        for t in np.arange(0.0, 12.0, 0.25):
            self.d.render(float(t)); W, H = SMALL
            bad += [(float(t), g) for g in self.d.reg.collisions()]
            bad += [(float(t), it[0]) for it in self.d.reg.items if it[1] < 0.035 * W - 1 or it[2] < 0.04 * H - 1 or it[3] > 0.965 * W + 1 or it[4] > 0.96 * H + 1]   # mobile_qa title-safe frame
        self.assertEqual(bad, [])

    def test_every_label_is_phone_sized_at_1080p(self):
        rec = []; textrec.STATE["rec"] = rec
        try:
            d = I.RadarGeometryDiagram((1920, 1080), 12.0)
            for t in (3.5, 8.2, 10.6): d.render(t)
        finally: textrec.STATE["rec"] = None
        self.assertTrue(rec); self.assertGreaterEqual(min(r["px"] for r in rec), 30.0)
        self.assertTrue(any(r["px"] >= 48 for r in rec))                                          # captions meet the repo's caption floor (mobile_qa.MIN_CAPTION_PX)

    def test_the_illustration_label_is_on_screen_from_the_start_to_the_end(self):
        for t in (0.6, 6.0, 11.0):
            self.d.render(t); self.assertTrue(any(i[0].startswith("chip_ILLUSTRATION") for i in self.d.reg.items), t)

    def test_exaggeration_label_appears_with_the_sinking(self):
        self.d.render(3.0); self.assertFalse(any("EXAGGERATED" in i[0] for i in self.d.reg.items)); self.d.render(6.0); self.assertTrue(any("EXAGGERATED" in i[0] for i in self.d.reg.items))

    def test_manifest_says_illustration_without_evidence_pixels(self):
        m = self.d.manifest(); self.assertEqual(m["kind"], "ILLUSTRATION"); self.assertFalse(m["evidence_pixels"])

    def test_camera_never_leaves_the_canvas(self):
        for t in np.arange(0, 12, 0.2):
            x0, y0, z = self.d.view(float(t)); self.assertGreaterEqual(x0, -1e-6); self.assertGreaterEqual(y0, -1e-6)
            self.assertLessEqual(x0 + 1920 / z, 1920 + 1e-6); self.assertLessEqual(y0 + 1080 / z, 1080 + 1e-6)


class TestEvidencePending(unittest.TestCase):
    def test_it_shows_no_data_and_says_so(self):
        p = I.EvidencePending(SMALL, 2.0); im = np.asarray(p.render(1.5), np.int16); self.assertFalse(p.manifest()["shows_data"])
        chroma = im.max(2) - im.min(2); self.assertLess(float((chroma > 70).mean()), 0.02)          # no colour scale, no heat map
        self.assertTrue(any("chip_PLACEHOLDER" in i[0] for i in p.reg.items)); self.assertTrue(any(i[0] == "title" for i in p.reg.items))

    def test_joins_a_flash_dip_in_a_sequence(self):
        seq = S.Sequence([S.Shot(I.RadarGeometryDiagram(SMALL, 12.0), 12.0), S.Shot(I.EvidencePending(SMALL, 2.0), 2.0)], [TR.FlashDip(0.5)])
        self.assertAlmostEqual(seq.duration, 13.5); self.assertEqual(seq.problems, []); self.assertEqual(seq.render(11.75).size, SMALL); self.assertEqual(seq.render(13.0).size, SMALL)


if __name__ == "__main__": unittest.main()
