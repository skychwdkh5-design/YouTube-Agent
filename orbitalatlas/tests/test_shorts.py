"""shorts + music: vertical-format helpers (image camera, tilted plane with anchored points, type, shape morph, safe zone) and the loopable score."""
import math, os, tempfile, unittest
import numpy as np
from PIL import Image
from orbitalatlas import shorts as SH, music, textrec as TR


def checker(w=800, h=800):
    a = np.zeros((h, w, 3), np.uint8); a[(np.arange(h)[:, None] // 40 + np.arange(w)[None, :] // 40) % 2 == 0] = 200; return Image.fromarray(a)


class TestImageView(unittest.TestCase):
    def test_centre_maps_to_screen_centre_and_scale_is_width(self):
        iv = SH.ImageView(checker()); x, y = iv.to_screen((0.5, 0.5), 0.5, 0.5, 400, size=(200, 300)); self.assertAlmostEqual(x, 100); self.assertAlmostEqual(y, 150)
        x2, _ = iv.to_screen((0.75, 0.5), 0.5, 0.5, 400, size=(200, 300)); self.assertAlmostEqual(x2 - x, 100)        # 200 source px over 400 visible -> 100 screen px

    def test_view_size(self):
        self.assertEqual(SH.ImageView(checker()).view(0.5, 0.5, 300, size=(108, 192)).size, (108, 192))

    def test_lerp_view_is_log_width(self):
        a, b = (0, 0, 100.0), (1, 1, 400.0); self.assertAlmostEqual(SH.lerp_view(a, b, 0.5)[2], 200.0, places=6)


class TestTiltedPlane(unittest.TestCase):
    def test_plane_covers_the_frame_at_any_tilt(self):
        iv = SH.ImageView(Image.new("RGB", (900, 900), (255, 0, 0)))
        for deg in (0, 15, 30, 40):
            img, _ = SH.tilted_view(iv, 0.5, 0.5, 200, deg, size=(200, 356))
            for p in ((0, 0), (199, 0), (0, 355), (199, 355), (100, 0)): self.assertEqual(img.getpixel(p), (255, 0, 0), (deg, p))

    def test_zero_tilt_mapping_equals_flat_view(self):
        iv = SH.ImageView(checker()); _, f = SH.tilted_view(iv, 0.5, 0.5, 400, 0.0, size=(200, 300))
        for p in ((0.5, 0.5), (0.6, 0.45), (0.3, 0.7)):
            a, b = f(p), iv.to_screen(p, 0.5, 0.5, 400, size=(200, 300)); self.assertAlmostEqual(a[0], b[0], places=6); self.assertAlmostEqual(a[1], b[1], places=6)

    def test_anchor_follows_the_warp(self):
        """a bright dot drawn in the source must appear where to_screen says, after the tilt."""
        src = Image.new("RGB", (1000, 1000), (0, 0, 0)); src.paste((255, 255, 255), (690, 290, 710, 310)); iv = SH.ImageView(src)
        img, f = SH.tilted_view(iv, 0.5, 0.5, 600, 28, size=(300, 534)); x, y = f((0.7, 0.3))
        a = np.asarray(img.convert("L"), float); ys, xs = np.nonzero(a > 128)
        self.assertLess(abs(xs.mean() - x), 2.0); self.assertLess(abs(ys.mean() - y), 2.0)

    def test_tilt_narrows_the_far_edge(self):
        _, f = SH.tilted_view(SH.ImageView(checker()), 0.5, 0.5, 400, 30, size=(200, 300))
        top = f((0.75, 0.25))[0] - f((0.25, 0.25))[0]; bot = f((0.75, 0.75))[0] - f((0.25, 0.75))[0]; self.assertLess(top, bot)


class TestShapesAndType(unittest.TestCase):
    def test_morph_endpoints(self):
        a = SH.star_polygon(0, 0, 100, 12, 0.0); b = SH.star_polygon(0, 0, 100, 12, 0.4)
        np.testing.assert_allclose(SH.morph(a, b, 0.0, 120), SH.resample(a, 120), atol=1e-6); np.testing.assert_allclose(SH.morph(a, b, 1.0, 120), SH.resample(b, 120), atol=1e-6)

    def test_star_depth_zero_is_a_circle(self):
        r = np.hypot(*np.asarray(SH.star_polygon(0, 0, 50, 16, 0.0), float).T); self.assertLess(r.max() - r.min(), 1e-6)

    def test_star_depth_makes_spikes(self):
        r = np.hypot(*np.asarray(SH.star_polygon(0, 0, 50, 16, 0.3), float).T); self.assertGreater(r.max() - r.min(), 10)

    def test_extrude_is_larger_than_front(self):
        front, _, _ = SH.word_tile("SEA", 80); ex = SH.extrude("SEA", 80, 12); self.assertGreater(ex.width, front.width); self.assertGreater(ex.height, front.height)

    def test_slam_settles(self):
        self.assertIsNone(SH.slam(0.9, 1.0)); s = SH.slam(5.0, 1.0); self.assertAlmostEqual(s[0], 1.0, places=3); self.assertEqual(s[1], 1.0); self.assertLess(s[2], 0.01)

    def test_place_records_only_settled_type(self):
        TR.STATE["rec"] = []; lay = Image.new("RGBA", (1080, 1920))
        t, _, _ = SH.word_tile("HELLO", 90); SH.place(lay, t, 540, 900, 1.6, 1.0, 6.0, record="HELLO", px=90); self.assertEqual(TR.STATE["rec"], [])
        SH.place(lay, t, 540, 900, 1.0, 1.0, 0.0, record="HELLO", px=90); self.assertEqual(len(TR.STATE["rec"]), 1); TR.STATE["rec"] = None

    def test_safe_check_flags_outside_text(self):
        bad = SH.check_safe([dict(text="X", px=60, box=(20, 1500, 300, 1560), tag=None)]); good = SH.check_safe([dict(text="Y", px=60, box=(200, 600, 800, 700), tag=None)])
        self.assertTrue(bad); self.assertFalse(good)


class TestMusic(unittest.TestCase):
    def test_score_length_and_level(self):
        x = music.score(4.0, 120.0, accents=(1.0,), seed=1); self.assertEqual(x.shape, (4 * music.SR, 2)); self.assertLessEqual(np.abs(x).max(), 0.9001)

    def test_score_is_deterministic(self):
        np.testing.assert_array_equal(music.score(2.0, 128.0, seed=3), music.score(2.0, 128.0, seed=3))

    def test_loop_seam_is_continuous(self):
        """the tail is wrapped onto the head: the jump at the loop point is no larger than normal sample-to-sample motion."""
        x = music.score(15.0, 128.0, seed=7); seam = np.abs(x[0] - x[-1]).max(); typical = np.percentile(np.abs(np.diff(x, axis=0)), 99.9)
        self.assertLess(seam, 4 * typical + 0.05)

    def test_mix_short_places_voice_and_normalises(self):
        d = tempfile.mkdtemp(); v = os.path.join(d, "v.wav"); t = np.arange(music.SR) / music.SR
        music._write(v, np.stack([0.3 * np.sin(2 * np.pi * 220 * t)] * 2, 1)); out = os.path.join(d, "m.wav")
        rep = music.mix_short(out, 3.0, music.score(3.0, 128.0), voice=[(v, 0.0, 1.0, 1.0)], cues=[dict(t=0.5, kind="impact")])
        self.assertEqual(rep["voice"][0]["at"], 1.0); self.assertTrue(os.path.getsize(out) > 1000); self.assertIn("CC0", rep["license"])


if __name__ == "__main__":
    unittest.main()
