"""raster3d: structured scene recording, grouping/export bundle, quadric tessellation, sky remap; a real render only if Chromium is present."""
import json, math, os, shutil, tempfile, unittest
import numpy as np
from orbitalatlas import pbrt3d as P, raster3d as RZ


class TestRecording(unittest.TestCase):
    def test_scene_records_meshes_materials_and_camera(self):
        s = P.Scene(); s.camera((0, -10, 2), (0, 0, 0), 40, (64, 36), 4); s.sun_sky("sky.pfm", (-1, -1, 1))
        b = P.box((0, 0, 0), (1, 1, 1)); s.mesh(b[0], b[1], s.material("coateddiffuse", (0.8, 0.2, 0.2), roughness=0.3), b[2], b[3])
        self.assertEqual(len(s.objects), 1); self.assertEqual(s.objects[0]["mat"]["kind"], "coateddiffuse"); self.assertEqual(s.cam["fov"], 40.0)
        self.assertAlmostEqual(float(np.linalg.norm(s.sun["dir"])), 1.0)

    def test_xform_applies_to_recorded_points_and_to_pbrt_text(self):
        s = P.Scene(); M = np.eye(4); M[:3, 3] = (10, 0, 0); b = P.box((0, 0, 0), (1, 1, 1))
        s.mesh(b[0], b[1], s.material("diffuse"), b[2], xform=M)
        self.assertAlmostEqual(float(s.objects[0]["P"][:, 0].min()), 10.0, places=5); self.assertIn("ConcatTransform", "\n".join(s.world))

    def test_quadrics_are_tessellated_where_pbrt_puts_them(self):
        s = P.Scene(); s.shape('Shape "sphere" "float radius" [2]', s.material("diffuse"), ["Translate 5 0 0"])
        Pp = s.objects[0]["P"]; np.testing.assert_allclose(np.linalg.norm(Pp - [5, 0, 0], axis=1), 2.0, atol=1e-4)
        s.shape('Shape "disk" "float radius" [3] "float innerradius" [2]', s.material("diffuse"), [])
        r = np.hypot(s.objects[1]["P"][:, 0], s.objects[1]["P"][:, 1]); self.assertGreaterEqual(r.min(), 2 - 1e-6); self.assertLessEqual(r.max(), 3 + 1e-6)


class TestExport(unittest.TestCase):
    def test_group_merges_same_material_and_keeps_counts(self):
        s = P.Scene(); m = s.material("diffuse", (0.5, 0.5, 0.5))
        for k in range(3): b = P.box((k, 0, 0), (k + 1, 1, 1)); s.mesh(b[0], b[1], m, b[2], b[3])
        g = RZ.group(s.objects); self.assertEqual(len(g), 1); self.assertEqual(len(g[0]["P"]), 72); self.assertEqual(int(g[0]["idx"].max()), 71)

    def test_bundle_round_trip(self):
        d = tempfile.mkdtemp(); s = P.Scene(); s.camera((0, -10, 2), (0, 0, 0), 40, (64, 36), 4); s.sun_sky("x", (0, -1, 1))
        b = P.box((0, 0, 0), (1, 1, 1)); s.mesh(b[0], b[1], s.material("diffuse"), b[2], b[3]); j = RZ.export_frame(s, os.path.join(d, "f"), (64, 36))
        doc = json.load(open(j)); g = doc["groups"][0]; raw = open(os.path.join(d, doc["bin"]), "rb").read()
        Pp = np.frombuffer(raw[g["P"][0]:g["P"][0] + g["P"][1]], np.float32).reshape(-1, 3); np.testing.assert_allclose(Pp, b[0], atol=1e-6); shutil.rmtree(d)


class TestSky(unittest.TestCase):
    def test_equal_area_mapping_is_unit_and_covers_both_hemispheres(self):
        c = (np.arange(64) + 0.5) / 64; U, V = np.meshgrid(c, c); d = RZ._equal_area_square_to_sphere(U, V)
        np.testing.assert_allclose(np.linalg.norm(d, axis=-1), 1.0, atol=1e-6); self.assertGreater(d[..., 2].max(), 0.95); self.assertLess(d[..., 2].min(), -0.95)
        self.assertAlmostEqual(float((d[..., 2] > 0).mean()), 0.5, delta=0.02)          # equal-area: half the texels per hemisphere


if __name__ == "__main__":
    unittest.main()
