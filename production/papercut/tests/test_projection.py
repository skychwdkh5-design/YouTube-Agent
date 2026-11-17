"""Regression tests for the ATLAS projection engine and the ATLAS layer.

    python3 -m unittest discover -s production/papercut/tests -p 'test_projection.py'
"""
import hashlib
import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from papercut import host as H  # noqa: E402
from papercut.atlas_layer import AtlasLayer  # noqa: E402
from papercut.projection import (ProjectionCue, ProjectionEngine, cues_from_dict, cues_from_script,  # noqa: E402
                                 resolve_anchor)

HAND = (355.0, 758.0)
CENTER = (505, 448)                    # middle of the approved box (330, 318, 680, 578)


def cues():
    return [ProjectionCue(0.0, 2.0, "EARTH TO ORION", "link"), ProjectionCue(2.0, 4.0, "SIGNAL BLOCKED", "blocked")]


def frame(col=(0, 0, 0)):
    return Image.new("RGBA", (1920, 1080), col + (255,))


class Cues(unittest.TestCase):
    def test_boundaries(self):
        e = ProjectionEngine(cues())
        self.assertEqual(e.active_cue(0).title, "EARTH TO ORION")
        self.assertEqual(e.active_cue(2).title, "SIGNAL BLOCKED")
        self.assertIsNone(e.active_cue(4))

    def test_rejections(self):
        with self.assertRaises(ValueError):
            ProjectionEngine([ProjectionCue(0, 2, "FIRST"), ProjectionCue(1, 3, "SECOND")])     # overlap
        with self.assertRaises(ValueError):
            ProjectionCue(1, 1, "WRONG")
        with self.assertRaises(ValueError):
            ProjectionCue(0, 1, "WRONG", "unknown")
        with self.assertRaises(ValueError):
            ProjectionCue(0, 2, "ONE TWO THREE FOUR FIVE")                                     # > 4 words
        with self.assertRaises(ValueError):
            ProjectionEngine([ProjectionCue(0, 2, "WWWWWWWWWWWWWWWWWWWW")])                    # does not fit at 22 px
        with self.assertRaises(ValueError):
            ProjectionEngine([ProjectionCue(0, 0.6, "TOO SHORT")])                             # unreadable page
        with self.assertRaises(ValueError):
            ProjectionEngine(cues(), box=(1700, 120, 2100, 380))                               # outside the frame

    def test_json_loading(self):
        self.assertEqual(cues_from_dict([{"start": 0, "end": 3, "title": "NASA ANIMATION", "kind": "flash"}])[0].kind, "flash")

    def test_script_anchors(self):
        words = [{"text": t, "start": 1.0 + i, "end": 1.5 + i} for i, t in
                 enumerate(["The", "Moon", "itself", "blocked", "the", "direct", "path.", "Wait", "for", "contact."])]
        self.assertEqual(resolve_anchor({"phrase": "direct PATH"}, words), 6.0)
        self.assertEqual(resolve_anchor({"phrase": "the", "occurrence": 2}, words), 5.0)
        self.assertEqual(resolve_anchor({"word": 3, "edge": "end", "offset": 0.1}, words), 4.6)
        with self.assertRaises(ValueError):
            resolve_anchor({"phrase": "not said"}, words)
        c = cues_from_script([{"at": {"phrase": "Moon itself"}, "title": "THE MOON", "kind": "dark"},
                              {"at": {"phrase": "blocked"}, "title": "NO DIRECT PATH", "kind": "blocked",
                               "until": {"phrase": "path.", "edge": "end"}},
                              {"at": {"phrase": "wait for contact"}, "title": "GROUND WAITS", "kind": "wait"}], words)
        self.assertEqual([(x.start, x.end) for x in c], [(1.85, 3.85), (3.85, 7.5), (7.85, 11.1)])
        e = ProjectionEngine(c)
        self.assertEqual(len(e.sessions), 2)            # `until` closes the panel, the next page reopens it


class Rendering(unittest.TestCase):
    def test_states_open_turn_close(self):
        e = ProjectionEngine(cues())
        st = {t: e.render(frame(), t, HAND)["state"] for t in (0.1, 1.0, 2.1, 3.0, 3.9)}
        self.assertEqual(st, {0.1: "opening", 1.0: "open", 2.1: "turning", 3.0: "open", 3.9: "closing"})
        self.assertIsNone(e.render(frame(), 4.0, HAND))

    def test_no_draw_outside_cue(self):
        e = ProjectionEngine([ProjectionCue(2.0, 4.0, "LATER", "label")])
        im = frame()
        self.assertIsNone(e.render(im, 1.0, HAND))
        self.assertEqual(im.getpixel(CENTER), (0, 0, 0, 255))

    def test_alpha_is_not_squared(self):
        """PR #57 pasted the panel with its own alpha as mask (alpha*alpha); the panel must be 93 % opaque."""
        e = ProjectionEngine(cues())
        black, white = frame(), frame((255, 255, 255))
        e.render(black, 1.0, HAND); e.render(white, 1.0, HAND)
        b = np.asarray(black, np.float32)[440:460, 480:530, :3]
        w = np.asarray(white, np.float32)[440:460, 480:530, :3]
        alpha = 1 - (w - b).mean() / 255                 # panel 0.93 over its own soft shadow
        self.assertGreater(alpha, 0.92)
        self.assertLess(alpha, 0.97)
        panel = e._panel(e.cues[0], 1.0)
        self.assertEqual(panel.getpixel((175, 130))[3], int(255 * 0.93))   # not 0.93 ** 2

    def test_steady_frames_come_from_cache(self):
        e = ProjectionEngine([ProjectionCue(0.0, 6.0, "DARK MOON", "dark")])
        for i in range(30, 150):
            e.render(frame(), i / 30, HAND)
        miss = e.stats["misses"]
        for i in range(150, 160):
            e.render(frame(), i / 30, HAND)
        self.assertEqual(e.stats["misses"], miss)        # a still page is drawn once

    def test_offscreen_hand_does_not_crash(self):
        e = ProjectionEngine(cues())
        self.assertIsNotNone(e.render(frame(), 0.05, (-80, 1300)))

    def test_matches_the_approved_projection(self):
        """Same look as the approved PR #56 scene on steady pages: mean difference < 1 level."""
        sys.path.insert(0, str(ROOT / "scenes"))
        import test20_projection as approved
        old = approved.Projection()
        starts = [p[0] for p in approved.PAGES] + [30.0]
        e = ProjectionEngine([ProjectionCue(starts[i], starts[i + 1], p[1], p[2]) for i, p in enumerate(approved.PAGES)],
                             box=approved.PANEL)
        rng = np.random.default_rng(3)
        bg = Image.fromarray(rng.integers(0, 255, (1080, 1920, 3), dtype=np.uint8)).convert("RGBA")
        for t in (3.0, 9.0, 12.0, 15.2, 18.0):          # steady pages (page turns are cleaner now, by design)
            a, b = bg.copy(), bg.copy()
            old.draw(a, t, HAND)
            e.render(b, t, HAND)
            d = np.abs(np.asarray(a, np.float32) - np.asarray(b, np.float32))[300:800, 300:700]
            self.assertLess(d.mean(), 1.0, f"t={t}")


class Host(unittest.TestCase):
    def test_region_composite_is_pixel_identical(self):
        """host._composite now works in the layer's region only; bytes must equal the old full-frame version."""
        rng = np.random.default_rng(5)
        base = Image.fromarray(rng.integers(0, 255, (1080, 1920, 4), dtype=np.uint8), "RGBA")
        layer = rng.random((300, 200, 4)).astype(np.float32)
        layer[..., :3] = np.minimum(layer[..., :3], layer[..., 3:4])

        def old(frame, layer, x0, y0, k):                       # the full-frame original (main @ f6564b8)
            W, Hh = frame.size
            dst = (np.asarray(frame, dtype=np.float32) / 255.0).copy()
            from PIL import ImageFilter
            sh = Image.fromarray((layer[..., 3] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5 * k / 2))
            sa = np.asarray(sh, dtype=np.float32) / 255.0 * 0.38
            H._over(dst, np.dstack([sa * 0.05, sa * 0.07, sa * 0.12, sa]), x0 + round(6 * k / 2), y0 + round(8 * k / 2), W, Hh)
            H._over(dst, layer, x0, y0, W, Hh)
            frame.paste(Image.fromarray((np.clip(dst, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA"))

        for x0, y0 in ((100, 600), (-50, 900), (1800, -40)):
            a, b = base.copy(), base.copy()
            old(a, layer, x0, y0, 2.0)
            H._composite(b, layer, x0, y0, True, 2.0)
            self.assertEqual(hashlib.sha256(a.tobytes()).digest(), hashlib.sha256(b.tobytes()).digest(), (x0, y0))


class Layer(unittest.TestCase):
    def test_atlas_layer(self):
        words = [{"text": t, "start": 0.2 + 0.4 * i, "end": 0.5 + 0.4 * i} for i, t in
                 enumerate("When Orion moved behind the Moon the Moon blocked the direct path".split())]
        spec = {"host": {"x": 250, "y": 985, "height": 400},
                "projection": {"pages": [{"at": {"phrase": "Orion moved"}, "title": "EARTH TO ORION", "kind": "link"},
                                         {"at": {"phrase": "blocked"}, "title": "NO DIRECT PATH", "kind": "blocked"}]}}
        layer = AtlasLayer.from_spec(spec, words, None, duration=6.0)
        self.assertEqual([p["title"] for p in layer.pages()], ["EARTH TO ORION", "NO DIRECT PATH"])
        im = frame((20, 30, 40))
        info = layer.render(im, 2.0)
        self.assertEqual(info["projection"]["page"], "EARTH TO ORION")
        self.assertEqual(info["drawing"].split(":")[0], "hero")          # the approved drawing, never a jointed rig
        bad = dict(spec, projection=dict(spec["projection"], box=[100, 600, 450, 860]))
        with self.assertRaises(ValueError):
            AtlasLayer.from_spec(bad, words, None, duration=6.0)


if __name__ == "__main__":
    unittest.main()
