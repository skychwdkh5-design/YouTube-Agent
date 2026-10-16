"""pbrt3d: scene writer, geometry helpers, PFM round trip, projection and the filmic finish (pure Python; pbrt itself is tested only if built)."""
import math, os, shutil, tempfile, unittest
import numpy as np
from orbitalatlas import pbrt3d as P


class TestGeometry(unittest.TestCase):
    def test_box_has_six_faces_and_outward_normals(self):
        Pp, I, N, UV = P.box((0, 0, 0), (2, 3, 4)); self.assertEqual(len(Pp), 24); self.assertEqual(len(I), 36)
        c = Pp.mean(0)
        for k in range(6):
            q = Pp[4 * k:4 * k + 4].mean(0); self.assertGreater(float((q - c) @ N[4 * k]), 0)

    def test_grid_is_the_height_field(self):
        xs, ys = np.linspace(-5, 5, 11), np.linspace(0, 4, 5); Pp, I, N, UV = P.grid(xs, ys, lambda X, Y: 0.1 * X)
        np.testing.assert_allclose(Pp[:, 2], 0.1 * Pp[:, 0]); self.assertEqual(len(I), (10 * 4) * 6)
        self.assertTrue(np.all(N[:, 2] > 0)); np.testing.assert_allclose(np.linalg.norm(N, axis=1), 1, atol=1e-6)

    def test_strip_spans_the_two_curves(self):
        xs = np.linspace(0, 10, 6); Pp, I, N, UV = P.strip(xs, -2 - 0 * xs, 1 + 0.1 * xs, 0.5)
        self.assertTrue(np.all(Pp[:, 1] == 0.5)); self.assertAlmostEqual(Pp[:, 2].min(), -2); self.assertAlmostEqual(Pp[:, 2].max(), 2.0)

    def test_tube_radius_and_merge(self):
        a, b = (0, 0, 0), (0, 0, 5); Pp, I, N = P.tube(a, b, 0.3)
        np.testing.assert_allclose(np.hypot(Pp[:, 0], Pp[:, 1]), 0.3, atol=1e-9)
        m = P.merge([P.tube(a, b, 0.3), P.tube((1, 0, 0), (1, 0, 5), 0.3)]); self.assertEqual(len(m[0]), 2 * len(Pp)); self.assertEqual(m[1].max(), 2 * len(Pp) - 1)


class TestCameraAndImages(unittest.TestCase):
    def test_project_centre_and_right(self):
        x, y, z = P.project((0, 10, 0), (0, 0, 0), (0, 1, 0), 40, (1920, 1080)); self.assertAlmostEqual(x, 960); self.assertAlmostEqual(y, 540); self.assertAlmostEqual(z, 10)
        x2, _, _ = P.project((1, 10, 0), (0, 0, 0), (0, 1, 0), 40, (1920, 1080)); self.assertGreater(x2, 960)     # +x is screen right (right-handed, z up)
        _, y2, _ = P.project((0, 10, 1), (0, 0, 0), (0, 1, 0), 40, (1920, 1080)); self.assertLess(y2, 540)         # up is screen up

    def test_pfm_round_trip(self):
        d = tempfile.mkdtemp(); a = np.random.default_rng(0).random((7, 9, 3)).astype(np.float32); P.write_pfm(os.path.join(d, "a.pfm"), a)
        np.testing.assert_array_equal(P.read_pfm(os.path.join(d, "a.pfm")), a); shutil.rmtree(d)

    def test_finish_range_and_monotone(self):
        ramp = np.repeat(np.linspace(0, 8, 64, dtype=np.float32)[None, :, None], 3, axis=2); out = P.finish(ramp, vignette=0, contrast=1.0)
        self.assertEqual(out.dtype, np.uint8); self.assertTrue(np.all(np.diff(out[0, :, 0].astype(int)) >= 0)); self.assertEqual(out[0, 0, 0], 0)

    def test_haze_only_on_geometry(self):
        hdr = np.zeros((2, 2, 3), np.float32); dist = np.array([[0, 100], [1e4, 1e5]], np.float32)
        out = P.finish(hdr, vignette=0, dist=dist, haze=(0.5, 0.5, 0.5), haze_m=1000.0)
        self.assertEqual(int(out[0, 0, 0]), 0); self.assertLess(int(out[0, 1, 0]), int(out[1, 0, 0]))


class TestSceneWriter(unittest.TestCase):
    def test_motion_blur_camera_and_no_negative_scale(self):
        s = P.Scene(); s.camera((0, -10, 2), (0, 0, 0), 40, (64, 36), 4, eye1=(0.1, -10, 2), target1=(0, 0, 0))
        txt = "\n".join(s.head); self.assertIn("ActiveTransform StartTime", txt); self.assertIn("ActiveTransform EndTime", txt)
        self.assertNotIn("Scale -1", txt)                         # a negative scale breaks the animated camera (blank frames): mirrored in post instead

    def test_mesh_emitter_lines(self):
        s = P.Scene(); m = P.box((0, 0, 0), (1, 1, 1)); s.mesh(m[0], m[1], s.material("diffuse", (0, 0, 0)), m[2], emit=(1, 2, 3), twosided=True)
        txt = "\n".join(s.world); self.assertIn('AreaLightSource "diffuse" "rgb L" [1 2 3] "bool twosided" true', txt); self.assertIn('"trianglemesh"', txt)

    @unittest.skipUnless(os.path.exists(os.path.join(P.PBRT_BIN, "pbrt")), "pbrt-v4 not built in this container")
    def test_tiny_render_is_not_blank(self):
        d = tempfile.mkdtemp(); s = P.Scene(); s.camera((0, -10, 3), (0, 0, 0.5), 40, (32, 18), 4, eye1=(0.2, -10, 3), target1=(0, 0, 0.5), film=os.path.join(d, "o.exr"))
        s.world.append('LightSource "distant" "point3 from" [-1 -1 2] "point3 to" [0 0 0] "rgb L" [3 3 3]')
        b = P.box((-1, -1, 0), (1, 1, 1)); s.mesh(b[0], b[1], s.material("diffuse", (0.8, 0.2, 0.2)), b[2])
        s.write(os.path.join(d, "s.pbrt")); P.render(os.path.join(d, "s.pbrt"))
        pf = P.exr_to_pfms(os.path.join(d, "o.exr"), os.path.join(d, "o")); self.assertGreater(float(P.read_pfm(pf["color"]).max()), 0.01); shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main()


class TestS3V3Presets(unittest.TestCase):
    """render presets of the reference true-3D production (productions/ep004-jakarta/proof_v3/run_v3.py)."""
    @classmethod
    def setUpClass(cls):
        import importlib.util, sys
        p = os.path.join(os.path.dirname(__file__), "../../productions/ep004-jakarta/proof_v3/run_v3.py")
        if not os.path.exists(p): raise unittest.SkipTest("reference production not present")
        sys.path.insert(0, os.path.dirname(os.path.abspath(p))); spec = importlib.util.spec_from_file_location("run_v3", p); cls.R = importlib.util.module_from_spec(spec); spec.loader.exec_module(cls.R)

    def test_presets_exist_and_keep_the_full_scene(self):
        for k in ("PREVIEW", "REVIEW", "FINAL"): self.assertIn(k, self.R.PRESETS)
        self.assertEqual(self.R.PRESETS["REVIEW"]["size"], (1280, 720)); self.assertEqual(self.R.PRESETS["FINAL"]["size"], (1920, 1080))

    def test_default_4_spp_and_8_only_under_depth_of_field(self):
        self.assertEqual(self.R.spp_for("REVIEW", 1.0), 4); self.assertEqual(self.R.spp_for("REVIEW", 5.5), 8); self.assertEqual(self.R.spp_for("REVIEW", 9.0), 4)
        for preset in ("REVIEW", "FINAL"):
            for t0, t1, n in self.R.SPP_OVERRIDES[preset]: self.assertGreaterEqual(n, 4)          # 2 spp was rejected for review/final
