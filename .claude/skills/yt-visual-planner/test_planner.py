#!/usr/bin/env python3
import json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import planner as pl

GRID = {"epsg": 32636, "x0": 706200.0, "y_top": 3116000.0, "pixel_m": 10.0, "width": 2180, "height": 928}
WIDE = dict(GRID, pixel_m=40.0, width=1000, height=500)
PROV = {"scenes": [{"id": f"y{y}", "datetime": f"{y}-10-1{y % 10}T08:00:00Z", "itemId": f"I{y}", "platform": "S2A"} for y in (2020, 2022, 2024, 2026)]}
CLAIMS = [
    {"id": "C1", "tier": "original", "text": "t", "short": "170 km announced", "confidence": "medium", "scale_km": 170},
    {"id": "C2", "tier": "media", "text": "t", "short": "A: 2.4 km by 2030", "confidence": "medium", "wording": "reported", "attribution": "A", "date": "2024-04-01"},
    {"id": "C3", "tier": "media", "text": "t", "short": "B: halted", "confidence": "medium", "wording": "reported", "attribution": "B", "date": "2026-05-22"},
    {"id": "C4", "tier": "media", "text": "t", "short": "C: low", "confidence": "low", "wording": "reported", "attribution": "C", "date": "2026-06-01"},
    {"id": "C5", "tier": "observation", "text": "t", "short": "Dark segment, 1.6 km", "confidence": "high", "years": [2022, 2026], "focus": [35.2165, 28.1062],
     "callouts": [{"at": [35.2093, 28.1062], "text": "Dark segment"}], "evidence": "e"},
    {"id": "C6", "tier": "observation", "text": "t", "short": "Pixel is 10 m", "confidence": "high", "visual": False, "evidence": "e"},
    {"id": "C7", "tier": "hypothesis", "text": "may", "short": "May be water", "confidence": "low"}]
SCRIPT = """## hook: Hook
Announced. {C1} Then observed. {C5}
## plan: Plan
Outlet reported. {C2} Another reported. {C3}
## method: Method
Pixel. {C6}
## segment: Segment
Zoom. {C5}
## limits: Limits
Not sure. {L} Maybe. {C7}
## close: Close
Bye.
"""


def make(d, claims=CLAIMS, script=SCRIPT, wide=True):
    os.makedirs(os.path.join(d, "research"))
    os.makedirs(os.path.join(d, "evidence", "stack"))
    json.dump(GRID, open(os.path.join(d, "evidence", "stack", "grid.json"), "w"))
    json.dump(PROV, open(os.path.join(d, "evidence", "stack", "provenance.json"), "w"))
    if wide:
        os.makedirs(os.path.join(d, "evidence", "wide"))
        json.dump(WIDE, open(os.path.join(d, "evidence", "wide", "grid.json"), "w"))
        json.dump({"scenes": [{"id": "y2026", "datetime": "2026-10-08T08:00:00Z"}]}, open(os.path.join(d, "evidence", "wide", "provenance.json"), "w"))
    stacks = [{"name": "stack", "aoi": [35.10, 28.07, 35.32, 28.15], "years": [2020, 2022, 2024, 2026]}] + ([{"name": "wide", "role": "wide", "aoi": [35.0, 28.0, 35.6, 28.3], "years": [2026]}] if wide else [])
    json.dump({"title": "T", "geo": {"focus": [35.215, 28.11], "segment": [35.2165, 28.1062], "wide_focus": [35.3, 28.14], "stacks": stacks}, "notes": []}, open(os.path.join(d, "research", "notes.json"), "w"))
    json.dump({"claims": claims}, open(os.path.join(d, "claims.json"), "w"))
    open(os.path.join(d, "script.md"), "w").write(script)


class Plan(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        make(self.d)
        self.ep, self.spec = pl.plan(self.d)

    def test_no_hand_json_needed_and_assets_exist(self):
        ids = {g["id"] for g in self.spec["graphics"]}
        self.assertIn("g_scale", ids)
        self.assertIn("g_reports", ids)
        self.assertIn("g_tiers", ids)
        for ch in self.ep["chapters"]:
            for v in ch["visuals"]:
                for a in ([v["asset"]] if "asset" in v else v["wipe"]):
                    self.assertIn(a, self.ep["assets"], (ch["id"], v))
        self.assertEqual([c["id"] for c in self.ep["chapters"]], ["hook", "plan", "method", "segment", "limits", "close"])

    def test_low_confidence_claims_never_drawn(self):
        text = json.dumps(self.spec)
        self.assertNotIn("C: low", text)
        g = next(g for g in self.spec["graphics"] if g["id"] == "g_reports")
        self.assertEqual(g["steps"], ["170 km announced", "A: 2.4 km by 2030", "B: halted"])

    def test_date_labels_come_from_provenance(self):
        labels = [v["label"]["text"] for ch in self.ep["chapters"] for v in ch["visuals"] if isinstance(v.get("label"), dict) and v["label"].get("exempt")]
        self.assertTrue(labels)
        self.assertTrue(all(l.startswith("OCT ") for l in labels))
        cmp = next(g for g in self.spec["graphics"] if g["type"] == "compare")
        self.assertEqual(cmp["left"]["label"], "OCT 2022")

    def test_graphics_declare_claims(self):
        for k, a in self.ep["assets"].items():
            if a.get("kind") == "graphic":
                self.assertTrue(a["claims"], k)
        self.assertEqual(self.ep["assets"]["g_scale"]["claims"], ["C1"])

    def test_visual_false_claim_attaches_no_shot_claims(self):
        meth = next(c for c in self.ep["chapters"] if c["id"] == "method")
        self.assertTrue(all("claims" not in v for v in meth["visuals"]))

    def test_close_is_compact(self):
        close = next(c for c in self.ep["chapters"] if c["id"] == "close")
        self.assertLessEqual(len(close["visuals"]), 3)

    def test_scale_arrow_uses_claim_length(self):
        g = next(g for g in self.spec["graphics"] if g["id"] == "g_scale")
        self.assertIn("170 km", g["arrows"][0]["label"])
        self.assertIn("170", g["title"])

    def test_compare_view_clamped_inside_stack(self):
        d = tempfile.mkdtemp()
        cl = json.loads(json.dumps(CLAIMS))
        cl[4]["focus"] = [35.10, 28.07]                       # corner of the stack
        make(d, cl)
        _, spec = pl.plan(d)
        c = next(g for g in spec["graphics"] if g["type"] == "compare")["left"]["geo"]["center"]
        self.assertGreater(c[0], 35.10)


class Short(unittest.TestCase):
    def test_short_chapter_gets_fewer_visuals_and_the_drop_is_reported(self):
        d = tempfile.mkdtemp()
        short = SCRIPT.replace("Bye.", "Bye.")                                        # 'close' has two words: about 0.8 s
        make(d, script=short)
        ep, _ = pl.plan(d)
        close = next(c for c in ep["chapters"] if c["id"] == "close")
        self.assertEqual(len(close["visuals"]), 1)
        self.assertTrue(any(x["chapter"] == "close" for x in ep["planner_dropped"]))


class Errors(unittest.TestCase):
    def test_missing_stack_is_reported(self):
        d = tempfile.mkdtemp()
        make(d)
        os.remove(os.path.join(d, "evidence", "stack", "grid.json"))
        with self.assertRaises(pl.PlanError):
            pl.plan(d)

    def test_no_wide_stack_means_no_scale_graphic(self):
        d = tempfile.mkdtemp()
        make(d, wide=False)
        _, spec = pl.plan(d)
        self.assertNotIn("g_scale", {g["id"] for g in spec["graphics"]})


if __name__ == "__main__":
    unittest.main()
