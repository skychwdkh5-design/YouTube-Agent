"""scene3d (perspective camera, path, painter) and subsidence3d (S3 V2): projection maths, physical consistency of the cut-away, LOS geometry,
text discipline (one label at a time, phone sizes, title-safe frame) and that the profile shot is truly side-on."""
import math, unittest
import numpy as np
from orbitalatlas import scene3d as S3, subsidence3d as SD, textrec, sequence as SQ, transitions as TR, illustrate as I

SMALL = (480, 270)


class TestCamera(unittest.TestCase):
    def test_target_projects_to_the_centre(self):
        c = S3.Camera3D((10, -50, 20), (3, 4, 5), 40, (1920, 1080)); p, z = c.project([(3, 4, 5)])
        self.assertAlmostEqual(p[0, 0], 960, places=6); self.assertAlmostEqual(p[0, 1], 540, places=6); self.assertGreater(z[0], 0)

    def test_up_is_up_and_right_is_right(self):
        c = S3.Camera3D((0, -100, 0), (0, 0, 0), 40); p, _ = c.project([(10, 0, 0), (0, 0, 10)])
        self.assertGreater(p[0, 0], 960); self.assertLess(p[1, 1], 540)

    def test_points_behind_have_negative_depth(self):
        c = S3.Camera3D((0, -100, 0), (0, 0, 0), 40); _, z = c.project([(0, -200, 0)]); self.assertLess(z[0], 0)

    def test_plane_parallel_to_the_image_keeps_angles(self):
        """camera looking along +y: a right angle drawn in the plane y=0 stays a right angle on screen (the profile-shot guarantee)."""
        c = S3.Camera3D((12, -70, 1), (12, 0, 1), 36); a, b, o = c.project([(5, 0, 3), (0, 0, -4), (0, 0, 3)])[0]
        v1, v2 = a - o, b - o; self.assertAlmostEqual(float(v1 @ v2), 0.0, places=6)

    def test_lens_shift_moves_the_picture_and_keeps_angles(self):
        c0 = S3.Camera3D((12, -70, 1), (12, 0, 1), 36); c1 = S3.Camera3D((12, -70, 1), (12, 0, 1), 36, shift=(0, -190))
        pts = [(5, 0, 3), (0, 0, -4), (0, 0, 3)]; a0, _ = c0.project(pts); a1, _ = c1.project(pts)
        self.assertTrue(np.allclose(a1 - a0, (0, -190))); v1, v2 = a1[0] - a1[2], a1[1] - a1[2]; self.assertAlmostEqual(float(v1 @ v2), 0.0, places=6)

    def test_looking_straight_down_does_not_break(self):
        c = S3.Camera3D((0, 0, 100), (0, 0, 0), 40); p, z = c.project([(0, 0, 0)]); self.assertTrue(np.isfinite(p).all())

    def test_path_hits_keys_and_moves_smoothly(self):
        P = S3.CameraPath([(0, (0, 0, 0), (1, 0, 0), 40), (1, (10, 0, 0), (11, 0, 0), 40), (2, (10, 5, 0), (11, 5, 0), 30)])
        self.assertTrue(np.allclose(P.state(1.0)[0], (10, 0, 0))); xs = [P.state(t)[0][0] for t in np.linspace(0, 1, 50)]
        self.assertTrue(all(b >= a - 1e-9 for a, b in zip(xs, xs[1:])))                     # monotone: no overshoot


class TestPainter(unittest.TestCase):
    def test_near_quad_covers_far_quad(self):
        cam = S3.Camera3D((0, -50, 0), (0, 0, 0), 40, SMALL); pa = S3.Painter(cam, fog_max=0.0)
        pa.poly([(-5, 10, -5), (5, 10, -5), (5, 10, 5), (-5, 10, 5)], (255, 0, 0), None)        # far, red
        pa.poly([(-5, 0, -5), (5, 0, -5), (5, 0, 5), (-5, 0, 5)], (0, 255, 0), None)            # near, green, added first would still win
        im = np.asarray(pa.render(S3.sky(SMALL)))
        self.assertGreater(int(im[135, 240, 1]), 200); self.assertLess(int(im[135, 240, 0]), 60)

    def test_lower_stage_is_drawn_first(self):
        cam = S3.Camera3D((0, -50, 0), (0, 0, 0), 40, SMALL); pa = S3.Painter(cam, fog_max=0.0)
        pa.stage = 2; pa.poly([(-5, 10, -5), (5, 10, -5), (5, 10, 5), (-5, 10, 5)], (255, 0, 0), None)   # far but later stage -> on top
        pa.stage = 1; pa.poly([(-5, 0, -5), (5, 0, -5), (5, 0, 5), (-5, 0, 5)], (0, 255, 0), None)
        im = np.asarray(pa.render(S3.sky(SMALL))); self.assertGreater(int(im[135, 240, 0]), 200)

    def test_lines_crossing_the_camera_are_clipped_not_dropped(self):
        cam = S3.Camera3D((0, -50, 0), (0, 0, 0), 40, SMALL); pa = S3.Painter(cam); pa.line([(0, -100, -2), (0, 100, -2)], (255, 255, 255), 2.0)
        self.assertEqual(len(pa.items), 1); self.assertTrue(all(np.isfinite(np.array(pa.items[0][2])).all() for _ in [0]))


class TestPhysics(unittest.TestCase):
    def setUp(self): self.d = SD.CutawayRadarDiagram(SMALL)

    def test_surface_lowering_equals_clay_loss(self):
        for t in (0.0, 6.0, 9.0):
            for x in (-40.0, -5.0, 0.0, 12.0):
                b = self.d.boundaries(x, 0.0, t); total = sum(th for _, th, _ in SD.LAYERS)
                clay = (8.0 - (b[2] - b[1])) + (12.0 - (b[4] - b[3]))
                self.assertAlmostEqual(-(b[-1]), clay, places=9)                                  # surface drop == clay thickness loss
                self.assertAlmostEqual(b[3] - b[2], 9.0, places=9)                                # the sand aquifer does not compact
                self.assertAlmostEqual(b[0], -total, places=9)

    def test_drop_at_the_point_is_the_declared_drop_and_starts_after_pumping(self):
        self.assertAlmostEqual(float(self.d.subs(0, 0, 12.0)), self.d.drop); self.assertEqual(float(self.d.subs(0, 0, self.d.tl["pump"][0])), 0.0)
        self.assertLessEqual(self.d.tl["pump"][0], self.d.tl["sink"][0])

    def test_confined_aquifer_head_stays_above_the_aquifer_top(self):
        top = self.d.boundaries(self.d.well_x, 0.0, 12.0)[3]; self.assertGreater(self.d.head(12.0), top)

    def test_second_echo_targets_the_lowered_point_and_los_is_cos_incidence(self):
        self.assertTrue(np.allclose(self.d.Pend, (0, 0, -self.d.drop)))
        S, P = self.d.sat, self.d.P0; inc = math.acos((S - P)[2] / np.linalg.norm(S - P))
        self.assertAlmostEqual(self.d.los_comp, self.d.drop * math.cos(inc), places=9)
        self.assertAlmostEqual(float((self.d.Pend - self.d.F) @ self.d.u_away), 0.0, places=9)  # right angle at the foot

    def test_profile_shot_is_side_on(self):
        for t in np.arange(10.0, 11.7, 0.1):
            p, q, _ = self.d.path.state(float(t)); v = (q - p) / np.linalg.norm(q - p); self.assertAlmostEqual(abs(v[1]), 1.0, places=6)

    def test_satellite_is_over_the_beam_plane_when_it_pings(self):
        for k in ("pulse1", "echo1", "pulse2", "echo2"):
            a, b = self.d.tl[k]
            for t in (a, (a + b) / 2): self.assertAlmostEqual(float(self.d.sat_pos(t)[1]), 0.0, places=6, msg=k)


class TestFrames(unittest.TestCase):
    def setUp(self): self.d = SD.CutawayRadarDiagram(SMALL)

    def test_determinism_and_size(self):
        a, b = self.d.render(6.0), self.d.render(6.0); self.assertEqual(a.size, SMALL); self.assertEqual(a.tobytes(), b.tobytes())

    def test_text_discipline(self):
        W, H = SMALL; bad = []
        for t in np.arange(0.0, 12.8, 0.25):
            self.d.render(float(t)); items = [i for i in self.d.reg.items if i[5] > 0.35]
            labels = [i for i in items if i[0] == "label"]; caps = [i for i in items if i[0] == "caption"]; lock = [i for i in items if i[0] == "lockup"]
            if len(labels) > 1 or len(caps) > 1 or (lock and caps): bad.append((float(t), "more than one message"))
            bad += [(float(t), g) for g in self.d.reg.collisions() if not g[0].startswith("chip") or not g[1].startswith("chip")]
            bad += [(float(t), it[0]) for it in items if it[1] < 0.035 * W - 1 or it[2] < 0.04 * H - 1 or it[3] > 0.965 * W + 1 or it[4] > 0.96 * H + 1]
        self.assertEqual(bad, [])

    def test_phone_sizes(self):
        rec = []; textrec.STATE["rec"] = rec
        try:
            d = SD.CutawayRadarDiagram((1920, 1080))
            for t in (1.5, 5.0, 6.5, 9.0, 11.3): d.render(t)
        finally: textrec.STATE["rec"] = None
        caps = [r for r in rec if r["tag"] == "WordCaptions"]; other = [r for r in rec if r["tag"] != "WordCaptions"]
        self.assertTrue(caps and other); self.assertGreaterEqual(min(r["px"] for r in caps), 48); self.assertGreaterEqual(min(r["px"] for r in other), 30)

    def test_illustration_chip_always_on(self):
        for t in (0.3, 5.0, 10.5): self.d.render(t); self.assertTrue(any(i[0].startswith("chip_ILLUSTRATION") for i in self.d.reg.items))

    def test_in_a_sequence_with_the_placeholder(self):
        seq = SQ.Sequence([SQ.Shot(self.d, 12.8), SQ.Shot(I.EvidencePending(SMALL, 1.3), 1.3)], [TR.Dissolve(0.6)])
        self.assertAlmostEqual(seq.duration, 13.5); self.assertEqual(seq.problems, []); self.assertEqual(seq.render(12.5).size, SMALL)


if __name__ == "__main__": unittest.main()
