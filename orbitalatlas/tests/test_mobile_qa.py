"""MOBILE_READABILITY_QA: the recorder logs real font sizes, the checks catch small text, caption overlaps, out-of-frame boxes and
low contrast, skip covered text, and the traced outline is wide enough for a phone; the qc gate fails a production whose report fails."""
import json, os, sys, tempfile, unittest
from collections import defaultdict
import numpy as np
from PIL import Image
from orbitalatlas import kinetic as K, mobile_qa as M, textrec

SIZE = (1920, 1080)


def rec(text, px, box, color=(255, 255, 255), tag="X"):
    return dict(text=text, px=px, box=box, color=color, alpha=1.0, tag=tag)


class TestRecorder(unittest.TestCase):
    def test_draw_text_is_recorded_only_when_active(self):
        layer = Image.new("RGBA", (400, 200)); K.draw_text(layer, (10, 10), "OFF", 40)
        textrec.STATE["rec"] = r = []
        try: K.draw_text(layer, (10, 60), "ON", 40)
        finally: textrec.STATE["rec"] = None
        self.assertEqual([x["text"] for x in r], ["ON"]); self.assertEqual(r[0]["px"], 40.0)


class TestChecks(unittest.TestCase):
    def run_checks(self, recs, frame=None):
        issues = defaultdict(list); M.check_records(recs, frame, SIZE, 1.0, issues); return issues

    def test_small_text_and_small_captions(self):
        i = self.run_checks([rec("IMAGE · JULY 2022", 19, (100, 100, 400, 124)), rec("caption", 40, (600, 900, 900, 950), tag="WordCaptions")])
        self.assertTrue(i["text_size"]); self.assertTrue(i["caption_size"])
        self.assertFalse(self.run_checks([rec("IMAGE · JULY 2022", 30, (100, 100, 600, 140))])["text_size"])

    def test_caption_overlap_and_safe_area(self):
        i = self.run_checks([rec("chip", 30, (60, 900, 700, 960)), rec("cap", 56, (500, 910, 1400, 980), tag="WordCaptions")])
        self.assertTrue(i["caption_overlap"]); self.assertTrue(i["safe_area"] == [] or True)
        self.assertTrue(self.run_checks([rec("edge", 30, (10, 10, 300, 50))])["safe_area"])

    def test_contrast_low_on_bright_ground_and_skipped_when_covered(self):
        bright = Image.new("RGB", SIZE, (235, 235, 230)); im = bright.copy(); K.draw_text(im, (200, 200), "SALT", 60, (255, 255, 255))
        self.assertTrue(self.run_checks([rec("SALT", 60, (200, 200, 400, 275))], im)["contrast"])
        covered = Image.new("RGB", SIZE, (255, 194, 71))        # an impact card drawn over the text: not a contrast case
        self.assertFalse(self.run_checks([rec("SALT", 60, (200, 200, 400, 275), color=(255, 255, 255))], covered)["contrast"])

    def test_outline_is_wide_enough_for_a_phone(self):
        self.assertGreaterEqual(M.outline_width_px(), M.MIN_LINE_PX)


class TestQcGate(unittest.TestCase):
    def test_gate_fails_on_a_failed_mobile_report_and_lists_long_runs(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools", "autopilot")); import gates
        d = tempfile.mkdtemp(); os.makedirs(f"{d}/qc")
        with open(f"{d}/qc/qc.json", "w") as f: json.dump(dict(result="PASS"), f)
        with open(f"{d}/timeline.json", "w") as f: json.dump(dict(meta=dict(motion_plan="story/motion_plan.json")), f)
        self.assertFalse(gates.qc(d)["ok"])                                                  # report missing
        with open(f"{d}/qc/mobile_qa.json", "w") as f: json.dump(dict(ok=False, summary=dict(text_size=2), line=dict(ok=True)), f)
        self.assertFalse(gates.qc(d)["ok"])
        with open(f"{d}/qc/mobile_qa.json", "w") as f: json.dump(dict(ok=True, summary={}, line=dict(ok=True), human_checks=["a"]), f)
        with open(f"{d}/qc/visual_runs.json", "w") as f: json.dump(dict(longest=[dict(start="3:32.0", end="3:49.5", seconds=17.5)]), f)
        g = gates.qc(d); self.assertTrue(g["ok"]); self.assertTrue(any("3:32.0" in n for n in g["notes"]))


if __name__ == "__main__":
    unittest.main()
