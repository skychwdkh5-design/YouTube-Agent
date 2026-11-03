"""Offline tests for tools/motion (no network). Run: python3 -m unittest tools/motion/test_motion.py"""
import math
import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compositor as C  # noqa: E402
import easing as E  # noqa: E402


class Easing(unittest.TestCase):
    def test_endpoints(self):
        for name, f in E.PRESETS.items():
            self.assertAlmostEqual(f(0), 0, places=6, msg=name)
            self.assertAlmostEqual(f(1), 1, places=6, msg=name)
            self.assertEqual(f(-1), f(0), name)
            self.assertEqual(f(2), f(1), name)

    def test_monotonic_where_expected(self):
        for name in ("linear", "v7_smoothstep", "enter", "exit", "move", "move_strong", "camera",
                     "reveal", "gravity", "topple"):   # springs overshoot by design
            v = [E.get(name)(i / 400) for i in range(401)]
            self.assertTrue(all(b >= a - 1e-9 for a, b in zip(v, v[1:])), name)

    def test_v7_parity(self):
        v7 = lambda x: (lambda x: x * x * (3 - 2 * x))(max(0, min(1, x)))
        for i in range(101):
            self.assertAlmostEqual(E.get("v7_smoothstep")(i / 100), v7(i / 100), places=12)

    def test_bezier_known_values(self):
        # CSS 'ease-in-out' cubic-bezier(.42,0,.58,1) is symmetric: f(.5) == .5
        f = E.cubic_bezier(.42, 0, .58, 1)
        self.assertAlmostEqual(f(.5), .5, places=5)
        self.assertAlmostEqual(f(.25) + f(.75), 1, places=5)
        # ease-out family is front-loaded
        self.assertGreater(E.get("enter")(.2), .6)
        self.assertLess(E.get("exit")(.2), .05)

    def test_shapes(self):
        self.assertLess(min(E.get("anticipate")(i / 100) for i in range(101)), -0.05)   # dips back
        self.assertGreater(max(E.get("settle_impact")(i / 100) for i in range(101)), 1.02)  # overshoots
        top = E.get("topple")
        # tipping: slow release, most of the angle in the last third
        self.assertLess(top(.5), .2)
        self.assertGreater(top(1) - top(.66), .5)

    def test_interpolate_and_convention(self):
        ks = [{"at": 0, "x": 0, "easing": "enter"}, {"at": 1, "x": 10, "easing": "linear"}, {"at": 2, "x": 20}]
        self.assertAlmostEqual(E.interpolate(ks, .5, "x"), 10 * E.get("enter")(.5))
        self.assertAlmostEqual(E.interpolate(ks, 1.5, "x"), 15)
        self.assertEqual(E.interpolate(ks, -1, "x"), 0)
        self.assertEqual(E.interpolate(ks, 9, "x"), 20)
        # no easing given -> V7 behaviour
        self.assertAlmostEqual(E.interpolate([{"at": 0, "x": 0}, {"at": 1, "x": 1}], .3, "x"), E.v7_smoothstep(.3))
        # vectors
        self.assertEqual(E.interpolate([{"at": 0, "p": [0, 0], "easing": "linear"}, {"at": 1, "p": [2, 4]}], .5, "p"), [1, 2])

    def test_unknown(self):
        with self.assertRaises(KeyError):
            E.get("bouncy")
        self.assertEqual(E.validate_names(["enter", "nope"]), ["nope"])


def dot(size=21):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    a = np.zeros((size, size), np.uint8)
    yy, xx = np.mgrid[0:size, 0:size]
    a[(xx - size // 2) ** 2 + (yy - size // 2) ** 2 <= (size // 2) ** 2] = 255
    im.putalpha(Image.fromarray(a))
    return im


def centroid(frame):
    a = np.asarray(frame.getchannel("A"), dtype=np.float64)
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    return (a * xx).sum() / a.sum(), (a * yy).sum() / a.sum()


class Compositor(unittest.TestCase):
    def test_render_follows_curve(self):
        """Pixels, not JSON: the rendered object position follows the named curve."""
        d = dot()
        ks = [{"at": 0, "x": 100.0, "easing": "enter"}, {"at": 1, "x": 900.0}]
        for t in (0.1, 0.25, 0.5, 0.8):
            fr = Image.new("RGBA", (1000, 200), (0, 0, 0, 0))
            p = C.place(d, (10, 10), (E.interpolate(ks, t, "x"), 100))
            fr.alpha_composite(p.image, p.xy)
            self.assertAlmostEqual(centroid(fr)[0], 100 + 800 * E.get("enter")(t), delta=1.0)

    def test_pivot_rotation(self):
        bar = Image.new("RGBA", (10, 100), (255, 255, 255, 255))
        p = C.place(bar, (5, 100), (200, 200), angle_deg=-90)   # base pivot, fall to the right
        fr = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
        fr.alpha_composite(p.image, p.xy)
        cx, cy = centroid(fr)
        self.assertAlmostEqual(cx, 250, delta=2)   # bar now lies to the right of the pivot
        self.assertAlmostEqual(cy, 200, delta=6)

    def test_bend_keeps_base(self):
        bar = Image.new("RGBA", (20, 200), (255, 255, 255, 255))
        b = C.bend(bar, base_y=199, amount_px=30, power=2)
        a = np.asarray(b.getchannel("A"))
        pad = b.info["bend_pad"]
        base_cols = np.nonzero(a[-1])[0]
        top_cols = np.nonzero(a[0])[0]
        self.assertAlmostEqual(base_cols.mean(), pad + 9.5, delta=1)
        self.assertAlmostEqual(top_cols.mean() - base_cols.mean(), 30, delta=2)

    def test_camera_never_upscales(self):
        cam = C.Camera(Image.new("RGB", (3000, 2000)))
        cam.frame(1500, 1000, 1920)
        with self.assertRaises(ValueError):
            cam.frame(1500, 1000, 1800)

    def test_parallax_depth(self):
        near = C.parallax((960, 540), (10, 0), 1.0, depth=1.5)
        far = C.parallax((960, 540), (10, 0), 1.0, depth=1.0)
        self.assertLess(near[0], far[0])   # closer layer moves further

    def test_ground_shadow_follows_pose(self):
        bar = Image.new("RGBA", (10, 200), (255, 255, 255, 255))
        def shadow_cx(angle):
            fr = Image.new("RGBA", (800, 400), (255, 255, 255, 255))
            C.ground_shadow(fr, C.place(bar, (5, 200), (300, 300), angle), 300, blur=1)
            a = 255 - np.asarray(fr.convert("L"), dtype=np.float64)
            yy, xx = np.mgrid[0:400, 0:800]
            return (a * xx).sum() / a.sum()
        self.assertGreater(shadow_cx(-40), shadow_cx(0) + 5)   # leaning right moves the shadow


if __name__ == "__main__":
    unittest.main()
