#!/usr/bin/env python3
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scene_templates as T


class Templates(unittest.TestCase):
    def test_every_template_expands_to_a_planner_scene_with_presets(self):
        f = [35.2, 28.1]
        cases = [
            {"template": "coast_pin", "id": "a", "chapter": "x", "asset": "y2026", "focus": f, "pin_at": f, "pin_text": "COAST", "anchor_text": "coast"},
            {"template": "pixel_zoom", "id": "b", "chapter": "x", "asset": "y2026", "focus": f, "anchor_text": "pixel", "pixel_m": 10, "arrow": {"from": f, "to": f, "text": "5 PIXELS = 50 M"}},
            {"template": "timelapse", "id": "c", "chapter": "x", "flip": ["y2020", "y2021"], "focus": f, "anchor_text": "seven"},
            {"template": "compare_instruments", "id": "d", "chapter": "x", "wipe": ["y2024", "l2024"], "focus": f, "anchor_text": "second", "wipe_at": "landsat", "label_a": "A", "label_b": "B"},
            {"template": "measure", "id": "e", "chapter": "x", "wipe": ["y2025", "y2026"], "focus": f, "anchor_text": "third", "arrows": [{"from": f, "to": f, "text": "ABOUT 1.6 KM", "anchor_text": "1.6"}]},
            {"template": "callout_zoom", "id": "g", "chapter": "x", "asset": "y2026", "focus": f, "anchor_text": "that fits", "pin_text": "HERE", "label": "NOT PROOF"},
        ]
        for c in cases:
            v = T.expand(c)
            self.assertEqual(v["id"], c["id"]); self.assertTrue(v["marks"] or v.get("label") or v.get("flip"), c["template"])
            self.assertGreater(v["min_s"], 0)
        self.assertEqual(T.expand(cases[1])["resample"], "nearest")              # explaining pixel size never smooths
        self.assertEqual(T.expand(cases[3])["resample"], "nearest")
        self.assertTrue(all(m.get("plate", True) for m in T.expand(cases[0])["marks"]))

    def test_unknown_template_or_missing_parameter_is_an_error(self):
        with self.assertRaises(T.TemplateError):
            T.expand({"template": "nope", "id": "a", "chapter": "x"})
        with self.assertRaises(T.TemplateError):
            T.expand({"template": "coast_pin", "id": "a", "chapter": "x", "asset": "y2026"})


if __name__ == "__main__":
    unittest.main()
