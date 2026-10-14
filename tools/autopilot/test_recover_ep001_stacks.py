#!/usr/bin/env python3
"""Offline tests for recover_ep001_stacks.py (no EP001 data needed)."""
import os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import recover_ep001_stacks as r  # noqa: E402

SRC = "import os\nS = '/old/scratch'\nW = S + '/landsat_work/ep001'\nSB = W + '/src_bands'\nOUT = S + '/acq/out'; os.makedirs(OUT, exist_ok=True)\n"


class Recover(unittest.TestCase):
    def test_grid_undoes_the_half_pixel_snap(self):
        g = r.grid_from_report({"grid": {"epsg": 32635, "x0": 100.0, "y_top": 500.0, "pixel_m": 30.0, "width": 3, "height": 4, "extra": 1}})
        self.assertEqual((g["x0"], g["y_top"]), (115.0, 485.0)); self.assertNotIn("extra", g)

    def test_paths_are_patched_and_nothing_else(self):
        out = r.patch_process(SRC, "/new/out", "/new/ws")
        self.assertIn("S = '/new/out'", out); self.assertIn("W = '/new/ws'", out); self.assertIn("OUT = S + '/out'", out); self.assertIn("SB = W + '/src_bands'", out)

    def test_unknown_layout_is_refused(self):
        with self.assertRaises(ValueError): r.patch_process("print('x')\n", "/a", "/b")

    def test_compare_names_the_differing_keys(self):
        self.assertTrue(r.compare({"a": 1}, {"a": 1})["identical"])
        c = r.compare({"a": 1, "b": 2}, {"a": 1, "b": 3}); self.assertFalse(c["identical"]); self.assertEqual(c["differing_keys"], ["b"])

    def test_output_directory_must_be_new(self):
        d = tempfile.mkdtemp(); open(os.path.join(d, "x"), "w").close()
        with self.assertRaises(ValueError): r.run(d, d, d)


if __name__ == "__main__":
    unittest.main()
