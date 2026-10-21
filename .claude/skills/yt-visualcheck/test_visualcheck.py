#!/usr/bin/env python3
import json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "yt-geo"))
import numpy as np, geostack as g
from PIL import Image
import visualcheck as vc

GRID = {"epsg": 32636, "x0": 706200.0, "y_top": 3116000.0, "pixel_m": 10.0, "width": 800, "height": 450}


def ll(c, r):
    lo, la = g.utm_to_lonlat(np.array([GRID["x0"] + c * 10]), np.array([GRID["y_top"] - r * 10]), GRID["epsg"])
    return [float(lo[0]), float(la[0])]


MID, FAR = ll(400, 225), ll(40, 20)
PROV = {"scenes": [{"id": f"y{y}", "datetime": f"{y}-10-08T08:00:00Z", "itemId": f"S2_{y}", "platform": p} for y, p in ((2022, "S2A"), (2024, "S2B"), (2026, "S2C"))]}


def claims(**over):
    base = [{"id": "C1", "tier": "observation", "text": "t", "confidence": "high", "short": "x", "check": {"kind": "ndwi_years", "file": "evidence/ndwi.json", "present": [2024, 2026], "absent": [2022], "min_px": 100},
             "anchor": MID},
            {"id": "C2", "tier": "observation", "text": "t", "confidence": "high", "short": "y"},
            {"id": "C3", "tier": "media", "text": "t", "confidence": "medium", "wording": "reported", "short": "z"},
            {"id": "C4", "tier": "observation", "text": "t", "confidence": "low", "short": "w"}]
    for c in base:
        c.update(over.get(c["id"], {}))
    return base


def make(d, ndwi=None, cl=None, labels=None, shots=None):
    os.makedirs(os.path.join(d, "story"))
    os.makedirs(os.path.join(d, "evidence", "stack"))
    for y in (2022, 2024, 2026):
        rng = np.random.default_rng(y)
        Image.fromarray(rng.integers(0, 255, (450, 800, 3), dtype=np.uint8)).save(os.path.join(d, "evidence", "stack", f"y{y}.png"))
    json.dump(GRID, open(os.path.join(d, "evidence", "stack", "grid.json"), "w"))
    json.dump(PROV, open(os.path.join(d, "evidence", "stack", "provenance.json"), "w"))
    json.dump({"years": ndwi or {"2022": {"water_like_px": 0, "extent_km": 0}, "2024": {"water_like_px": 500, "extent_km": 1.6}, "2026": {"water_like_px": 900, "extent_km": 1.9}}},
              open(os.path.join(d, "evidence", "ndwi.json"), "w"))
    json.dump({"claims": cl or claims()}, open(os.path.join(d, "claims.json"), "w"))
    json.dump({"grid": "evidence/stack/grid.json", "graphics": "g.json", "evidence": {"stacks": [{"name": "stack"}]},
               "assets": {f"y{y}": {"src": f"evidence/stack/y{y}.png"} for y in (2022, 2024, 2026)}}, open(os.path.join(d, "episode.json"), "w"))
    json.dump({"graphics": []}, open(os.path.join(d, "g.json"), "w"))
    json.dump({"shots": shots or [{"id": "s1", "info": "image", "claims": ["C1"], "camera": {"to": {"center": MID, "width_km": 3}}, "layers": [{"type": "image", "asset": "y2026"}]}]},
              open(os.path.join(d, "story", "storyboard.json"), "w"))
    json.dump(labels or [], open(os.path.join(d, "story", "labels.json"), "w"))


def status(d):
    r = vc.run(d)
    return r, {i["id"]: i["status"] for i in r["items"]}


class Checks(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def test_date_label_verified_against_metadata(self):
        make(self.d, labels=[{"text": "OCT 2026", "shot": "s1", "exempt": True}, {"text": "MAR 2026", "shot": "s1", "exempt": True}])
        _, st = status(self.d)
        self.assertEqual(st["s1:label:OCT 2026"], "VERIFIED_DATA")
        self.assertEqual(st["s1:label:MAR 2026"], "FAIL")                               # wrong month: caught

    def test_measured_data_and_location_verified(self):
        make(self.d)
        r, st = status(self.d)
        self.assertEqual(st["s1:shot"], "VERIFIED_DATA")
        self.assertIn("not machine-judged", r["items"][0]["why"])

    def test_view_not_containing_location_is_not_verified(self):
        make(self.d, shots=[{"id": "s1", "info": "x", "claims": ["C1"], "camera": {"to": {"center": FAR, "width_km": 1.0}}, "layers": [{"type": "image", "asset": "y2026"}]}])
        _, st = status(self.d)
        self.assertEqual(st["s1:shot"], "NEEDS_VISUAL_REVIEW")

    def test_contradicting_data_fails(self):
        make(self.d, ndwi={"2022": {"water_like_px": 900, "extent_km": 1.0}, "2024": {"water_like_px": 500, "extent_km": 1.6}, "2026": {"water_like_px": 900, "extent_km": 1.9}})
        self.assertEqual(status(self.d)[1]["s1:shot"], "FAIL")

    def test_no_machine_check_needs_review_and_writes_frame(self):
        make(self.d, shots=[{"id": "s1", "info": "x", "claims": ["C2"], "camera": {"to": {"center": MID, "width_km": 3}}, "layers": [{"type": "image", "asset": "y2026"}]}])
        r, st = status(self.d)
        self.assertEqual(st["s1:shot"], "NEEDS_VISUAL_REVIEW")
        self.assertTrue(os.path.exists(os.path.join(self.d, r["items"][0]["frames"][0]["file"])))
        self.assertEqual(r["overall"], "NEEDS_VISUAL_REVIEW")

    def test_low_confidence_claim_fails(self):
        make(self.d, shots=[{"id": "s1", "info": "x", "claims": ["C4"], "camera": {"to": {"center": MID, "width_km": 3}}, "layers": [{"type": "image", "asset": "y2026"}]}])
        self.assertEqual(status(self.d)[1]["s1:shot"], "FAIL")

    def test_label_without_claim_fails_and_attributed_text_is_source_verified(self):
        make(self.d, labels=[{"text": "Big claim", "shot": "s1"}, {"text": "Outlet reported", "shot": "s1", "claim": "C3"}])
        st = status(self.d)[1]
        self.assertEqual(st["s1:label:Big claim"], "FAIL")
        self.assertEqual(st["s1:label:Outlet reported"], "VERIFIED_SOURCE")


class Totals(unittest.TestCase):
    def test_total_equals_sum_of_counts_and_orphans_are_reported(self):
        d = tempfile.mkdtemp()
        make(d, labels=[{"text": "OCT 2026", "shot": "s1", "exempt": True}])
        os.makedirs(os.path.join(d, "qa"))
        json.dump({"reviews": [{"item": "x", "frame_sha256": "a" * 64, "claims": ["C9"], "reviewer": "agent", "verdict": "supports", "note": "n" * 25}]}, open(os.path.join(d, "qa", "visual_review.json"), "w"))
        r = vc.run(d)
        self.assertEqual(r["total"], len(r["items"]))
        self.assertEqual(sum(r["counts"].values()), r["total"])
        self.assertEqual(r["orphan_reviews"], 1)
        self.assertEqual(vc.prune_reviews(d)["removed"], 1)

    def test_missing_item_is_a_fail_not_a_silent_skip(self):
        d = tempfile.mkdtemp()
        make(d, labels=[{"text": "OCT 2026", "shot": "s1", "exempt": True}])
        sbp = os.path.join(d, "story", "storyboard.json")
        sb = json.load(open(sbp))
        sb["shots"].append({"id": "ghost", "info": "x", "claims": [], "layers": [{"type": "image", "asset": "y2026"}]})   # no claims: legitimately not audited
        json.dump(sb, open(sbp, "w"))
        lp = os.path.join(d, "story", "labels.json")
        json.dump(json.load(open(lp)) + [{"text": "Mystery", "shot": "nope"}], open(lp, "w"))                          # a label on an unknown shot: must still be audited
        r = vc.run(d)
        self.assertEqual(r["overall"], "FAIL")


class Cards(unittest.TestCase):
    """EP005 visual revision: a stepped card/diagram/chart has no map - its finished picture is the frame a reviewer must read."""
    def setUp(self):
        self.d = tempfile.mkdtemp()
        make(self.d, labels=[{"text": "graphic:card_s1", "claims": ["C2"], "exempt": False, "shot": "s1"}],
             shots=[{"id": "s1", "info": "card", "claims": ["C2"], "layers": [{"type": "graphic", "asset": "card_s1"}, {"type": "graphic", "asset": "card", "t": [3, None]}]}])
        os.makedirs(os.path.join(self.d, "graphics"))
        Image.fromarray(np.full((1080, 1920, 3), 30, dtype=np.uint8)).save(os.path.join(self.d, "graphics", "card.png"))
        Image.fromarray(np.full((1080, 1920, 3), 20, dtype=np.uint8)).save(os.path.join(self.d, "graphics", "card.step1.png"))
        ep = json.load(open(os.path.join(self.d, "episode.json")))
        ep["assets"]["card_s1"] = {"src": "graphics/card.step1.png", "kind": "graphic", "group": "card", "claims": ["C2"]}
        ep["assets"]["card"] = {"src": "graphics/card.png", "kind": "graphic", "group": "card", "claims": ["C2"]}
        json.dump(ep, open(os.path.join(self.d, "episode.json"), "w"))
        json.dump({"graphics": [{"id": "card", "type": "diagram", "title": "Card"}]}, open(os.path.join(self.d, "g.json"), "w"))

    def test_a_card_needs_a_reviewer_who_sees_the_final_picture_and_the_review_is_bound_to_it(self):
        r, st = status(self.d)
        self.assertEqual(st["s1:graphic:card_s1"], "NEEDS_VISUAL_REVIEW")
        self.assertEqual(r["items"][0]["frames"][0]["stack"], "graphics/card.png")           # the finished picture, not the first build step
        vc.add_review(self.d, "s1:graphic:card_s1", "supports", "Two boxes with the claimed wording and numbers are visible.", "agent")
        self.assertEqual(status(self.d)[1]["s1:graphic:card_s1"], "REVIEWED_BY_AGENT")
        Image.fromarray(np.full((1080, 1920, 3), 99, dtype=np.uint8)).save(os.path.join(self.d, "graphics", "card.png"))      # the card is redrawn
        self.assertEqual(status(self.d)[1]["s1:graphic:card_s1"], "NEEDS_VISUAL_REVIEW")


class Reviews(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        make(self.d, shots=[{"id": "s1", "info": "x", "claims": ["C2"], "camera": {"to": {"center": MID, "width_km": 3}}, "layers": [{"type": "image", "asset": "y2026"}]}])
        vc.run(self.d)

    def test_review_makes_it_reviewed_not_verified(self):
        vc.add_review(self.d, "s1:shot", "supports", "I saw a long straight light line across the frame.", "agent")
        r = vc.run(self.d)
        self.assertEqual(r["items"][0]["status"], "REVIEWED_BY_AGENT")
        self.assertEqual(r["overall"], "OK")
        self.assertNotIn("VERIFIED", r["items"][0]["status"])

    def test_review_is_bound_to_the_frame(self):
        vc.add_review(self.d, "s1:shot", "supports", "I saw a long straight light line across the frame.", "agent")
        Image.fromarray(np.zeros((450, 800, 3), dtype=np.uint8)).save(os.path.join(self.d, "evidence", "stack", "y2026.png"))   # the picture changes
        r = vc.run(self.d)
        self.assertEqual(r["items"][0]["status"], "NEEDS_VISUAL_REVIEW")

    def test_negative_review_blocks(self):
        vc.add_review(self.d, "s1:shot", "does_not_support", "The frame shows only bare ground, no line at all.", "agent")
        self.assertEqual(vc.run(self.d)["overall"], "FAIL")

    def test_unclear_review_does_not_pass(self):
        vc.add_review(self.d, "s1:shot", "unclear", "Cannot tell at this size whether there is a line.", "agent")
        self.assertEqual(vc.run(self.d)["overall"], "NEEDS_VISUAL_REVIEW")

    def test_review_needs_a_real_note(self):
        with self.assertRaises(ValueError):
            vc.add_review(self.d, "s1:shot", "supports", "ok", "agent")

    def test_wipe_needs_both_frames_reviewed(self):
        make(os.path.join(self.d, "w") if False else tempfile.mkdtemp(), shots=[])
        d = tempfile.mkdtemp()
        make(d, shots=[{"id": "s1", "info": "w", "claims": ["C2"], "camera": {"to": {"center": MID, "width_km": 3}}, "layers": [{"type": "image", "asset": "y2022"}, {"type": "wipe", "from": "y2022", "to": "y2026"}]}])
        vc.run(d)
        vc.add_review(d, "s1:shot", "supports", "The 2022 frame shows only bare ground here.", "agent", 0)
        self.assertEqual(vc.run(d)["overall"], "NEEDS_VISUAL_REVIEW")                 # the 2026 frame is still unseen
        vc.add_review(d, "s1:shot", "supports", "The 2026 frame shows a straight dark line here.", "agent", 1)
        self.assertEqual(vc.run(d)["overall"], "OK")


if __name__ == "__main__":
    unittest.main()
