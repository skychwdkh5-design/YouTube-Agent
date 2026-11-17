"""Standalone regression tests: python3 -m unittest discover -s production/papercut/tests -p 'test_projection.py'"""
import sys
import unittest
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from papercut.projection import ProjectionCue, ProjectionEngine, cues_from_dict


class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.engine = ProjectionEngine([
            ProjectionCue(0.0, 2.0, "EARTH TO ORION", "link"),
            ProjectionCue(2.0, 4.0, "SIGNAL BLOCKED", "blocked"),
        ], box=(180, 120, 530, 380))

    def test_cue_boundary(self):
        self.assertEqual(self.engine.active_cue(0).title, "EARTH TO ORION")
        self.assertEqual(self.engine.active_cue(2).title, "SIGNAL BLOCKED")
        self.assertIsNone(self.engine.active_cue(4))

    def test_render_and_cache(self):
        im = Image.new("RGBA", (640,480), (0,0,0,255))
        a = self.engine.render(im, 0.8, (100,370))
        self.assertEqual(a["kind"], "link")
        self.assertNotEqual(im.getpixel((350,245)), (0,0,0,255))
        self.assertEqual(len(self.engine._panels), 1)
        self.engine.render(im, 1.0, (100,370))
        self.assertEqual(len(self.engine._panels), 1)

    def test_no_draw_outside_active_cue(self):
        im = Image.new("RGBA", (640,480), (0,0,0,255))
        self.assertIsNone(self.engine.render(im, 8.0, (100,370)))
        self.assertEqual(im.getpixel((350,245)), (0,0,0,255))

    def test_overlap_rejected(self):
        with self.assertRaises(ValueError):
            ProjectionEngine([ProjectionCue(0,2,"FIRST"),ProjectionCue(1,3,"SECOND")])

    def test_invalid_cue_rejected(self):
        with self.assertRaises(ValueError):
            ProjectionCue(1,1,"WRONG")
        with self.assertRaises(ValueError):
            ProjectionCue(0,1,"WRONG","unknown")

    def test_json_loading(self):
        cues=cues_from_dict([{"start":0,"end":3,"title":"NASA ANIMATION","kind":"flash"}])
        self.assertEqual(cues[0].kind,"flash")

    def test_out_of_bounds_fails_closed(self):
        e=ProjectionEngine([ProjectionCue(0,1,"TEST")],box=(500,120,900,380))
        with self.assertRaises(ValueError):
            e.render(Image.new("RGBA",(640,480)),0.5,(100,370))

if __name__ == "__main__":
    unittest.main()
