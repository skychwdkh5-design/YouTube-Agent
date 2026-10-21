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

    def test_year_visuals_are_flagged_for_narration_anchoring(self):
        """The hook's year beats must follow the narrator's words (storyboard anchors them); an establishing beat precedes them."""
        hook = next(c for c in self.ep["chapters"] if c["id"] == "hook")["visuals"]
        flagged = [v for v in hook if v.get("anchor") == "year"]
        self.assertTrue(any("wipe" in v for v in flagged))
        self.assertTrue(any(v.get("asset") == "y2022" for v in flagged))
        first_map = next(v for v in hook if v.get("kind") != "graphic")
        self.assertEqual(first_map["asset"], "y2020")                    # establishing beat: earliest scene, not anchored
        self.assertNotEqual(first_map.get("anchor"), "year")

    def test_credit_is_printed_once(self):
        """The renderer's credit pill is the single credit on screen: geo graphics do not print their own."""
        for g in self.spec["graphics"]:
            if g["type"] == "geo":
                self.assertIs(g.get("show_credit"), False, g["id"])
                self.assertNotIn("· 20", g.get("date", ""))                 # date is a real scene date label, never a repeated year

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
        self.assertLessEqual(len(close["visuals"]), 6)                     # tiers, one recap wipe, hero graphic, closing view: never a replay of the film
        fams = [v.get("family") or v.get("asset") for v in close["visuals"]]
        self.assertEqual(len(fams), len(set(fams)))

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


class Media(unittest.TestCase):
    """VISUAL_STYLE_V3: verified real media enters the plan; anything else is listed as pending and never drawn."""
    def setUp(self):
        from PIL import Image
        self.d = tempfile.mkdtemp()
        make(self.d)
        os.makedirs(os.path.join(self.d, "media", "assets"))
        self.png = os.path.join(self.d, "media", "assets", "p.jpg")
        Image.new("RGB", (1600, 900), (120, 90, 60)).save(self.png)
        import hashlib
        self.sha = hashlib.sha256(open(self.png, "rb").read()).hexdigest()

    def ledger(self, **k):
        e = {"id": "p", "scene": "segment", "title": "Shore photo", "page_url": "https://example.org/p", "author": "A. Author", "license": "Public Domain", "kind": "photo", "status": "VERIFIED",
             "local_path": "media/assets/p.jpg", "sha256": self.sha, "retrieved": "2026-10-21", "attribution_text": "Shore photo / A. Author / Public Domain", "depicts_reality": True}
        e.update(k)
        json.dump({"schema": "yt-media-ledger/1", "entries": [e]}, open(os.path.join(self.d, "media", "ledger.json"), "w"))

    def stills(self, ep):
        return [v for c in ep["chapters"] for v in c["visuals"] if v.get("kind") == "still"]

    def test_verified_media_becomes_a_still_with_full_provenance(self):
        self.ledger()
        ep, _ = pl.plan(self.d)
        st = self.stills(ep)
        self.assertEqual(len(st), 1)
        a = ep["assets"][st[0]["asset"]]
        for k in ("src", "credit", "source_url", "license", "retrieved"):
            self.assertTrue(a[k])
        self.assertEqual(a["kind"], "external_still")
        self.assertEqual(ep["media_pending"], [])

    def test_unverified_or_tampered_media_is_never_drawn(self):
        for kw in ({"status": "UNVERIFIED"}, {"status": "DISCOVERED"}, {"status": "NEEDS_OWNER"}, {"status": "REJECTED"}, {"sha256": "0" * 64}, {"local_path": "media/assets/missing.jpg"}):
            self.ledger(**kw)
            ep, _ = pl.plan(self.d)
            self.assertEqual(self.stills(ep), [], kw)
            self.assertEqual(len(ep["media_pending"]), 1, kw)

    def test_verified_video_becomes_a_video_visual(self):
        self.ledger(kind="video", local_path="media/assets/p.jpg")          # stand-in file: the planner only checks presence and sha256
        ep, _ = pl.plan(self.d)
        vids = [v for c in ep["chapters"] for v in c["visuals"] if v.get("kind") == "video"]
        self.assertEqual(len(vids), 1)
        self.assertEqual(ep["assets"][vids[0]["asset"]]["kind"], "video")

    def test_rendering_carries_its_label(self):
        self.ledger(kind="rendering", on_screen_label="ARTIST'S RENDERING", depicts_reality=False)
        ep, _ = pl.plan(self.d)
        self.assertEqual(self.stills(ep)[0]["label"]["text"], "ARTIST'S RENDERING")

    def test_no_ledger_is_fine_and_long_map_runs_are_reported_as_gaps(self):
        ep, _ = pl.plan(self.d)
        self.assertEqual(ep["media_pending"], [])
        self.assertIsInstance(ep["media_gaps"], list)


class Infographics(unittest.TestCase):
    """Scenes written in notes.json: placed first in their chapter, anchored by words, never drawn on weak ground."""
    def setUp(self):
        self.d = tempfile.mkdtemp()
        make(self.d)
        self.n = json.load(open(os.path.join(self.d, "research", "notes.json")))

    def go(self, items):
        self.n["infographics"] = items
        json.dump(self.n, open(os.path.join(self.d, "research", "notes.json"), "w"))
        return pl.plan(self.d)

    def card(self, **k):
        d = {"id": "i_card", "chapter": "plan", "claims": ["C2"], "min_s": 8,
             "graphic": {"type": "diagram", "title": "T", "source": "S", "nodes": [{"id": "a", "text": "A", "x": 0.5, "y": 0.5, "step": 1}, {"id": "b", "text": "B", "x": 0.5, "y": 0.8, "step": 2}]},
             "steps": [{"anchor_text": "Outlet reported"}, {"anchor_text": "Another reported"}]}
        d.update(k)
        return d

    def test_stepped_graphic_gets_one_asset_per_step_in_one_group_and_leads_its_chapter(self):
        ep, spec = self.go([self.card()])
        v = next(c for c in ep["chapters"] if c["id"] == "plan")["visuals"][0]
        self.assertEqual([s["asset"] for s in v["steps"]], ["i_card_s1", "i_card"])
        self.assertEqual(v["steps"][0]["anchor_text"], "Outlet reported")
        for a in ("i_card_s1", "i_card"):
            self.assertEqual(ep["assets"][a]["group"], "i_card")
            self.assertEqual(ep["assets"][a]["claims"], ["C2"])
        self.assertIn("i_card", {g["id"] for g in spec["graphics"]})

    def test_unknown_claim_is_an_error_and_low_confidence_is_dropped_and_reported(self):
        with self.assertRaises(pl.PlanError):
            self.go([self.card(claims=["C99"])])
        ep, spec = self.go([self.card(claims=["C4"])])
        self.assertEqual([d["id"] for d in ep["infographics_dropped"]], ["i_card"])
        self.assertNotIn("i_card", {g["id"] for g in spec["graphics"]})

    def test_media_that_is_not_verified_is_dropped(self):
        g = {"type": "compare", "title": "T", "source": "S", "left": {"file": "media/assets/x.jpg", "label": "L", "credit": "C"}, "right": {"file": "media/assets/x.jpg", "label": "L", "credit": "C"}}
        ep, _ = self.go([{"id": "i_c", "chapter": "plan", "claims": ["C2"], "graphic": g}])
        self.assertIn("not VERIFIED", ep["infographics_dropped"][0]["reason"])

    def test_hook_and_close_are_built_by_rule_so_a_scene_placed_there_is_reported_not_lost(self):
        ep, _ = self.go([self.card(chapter="hook")])
        self.assertIn("built by rule", ep["infographics_dropped"][0]["reason"])

    def test_a_scene_that_closes_its_chapter_is_not_followed_by_a_filler_map_beat(self):
        ep0, _ = self.go([self.card(chapter="method", claims=[], exempt=True)])
        ep1, _ = self.go([self.card(chapter="method", claims=[], exempt=True, closes_chapter=True)])
        maps = lambda ep: len([v for c in ep["chapters"] if c["id"] == "method" for v in c["visuals"] if v.get("kind") not in ("graphic", "still", "video")])
        self.assertLessEqual(maps(ep1), maps(ep0))
        if maps(ep0) > 1:
            self.assertEqual(maps(ep1), maps(ep0) - 1)
            self.assertTrue(any(d.get("reason") == "a scene closes this chapter" for d in ep1["planner_dropped"]))

    def test_author_can_cap_the_map_beats_of_a_chapter_carried_by_scenes(self):
        self.n["max_map_beats"] = {"plan": 1}
        ep, _ = self.go([self.card()])
        maps = [v for c in ep["chapters"] if c["id"] == "plan" for v in c["visuals"] if v.get("kind") not in ("graphic", "still", "video")]
        self.assertLessEqual(len(maps), 1)

    def test_exempt_flag_reaches_every_step_asset(self):
        ep, _ = self.go([self.card(claims=[], exempt=True)])
        self.assertTrue(ep["assets"]["i_card_s1"]["exempt"] and ep["assets"]["i_card"]["exempt"])

    def test_ref_places_an_existing_graphic_at_a_sentence_and_the_claim_rules_do_not_repeat_it(self):
        ep, _ = self.go([{"id": "i_t", "chapter": "plan", "ref": "g_tiers", "anchor_text": "Outlet reported", "min_s": 6}])
        uses = [v for c in ep["chapters"] for v in c["visuals"] if v.get("asset") == "g_tiers"]
        self.assertEqual(len(uses), 1)
        self.assertEqual(uses[0]["anchor_text"], "Outlet reported")


class Media2(unittest.TestCase):
    def test_media_shown_inside_an_infographic_is_not_also_a_full_frame_still(self):
        from PIL import Image
        import hashlib
        d = tempfile.mkdtemp()
        make(d)
        os.makedirs(os.path.join(d, "media", "assets"))
        png = os.path.join(d, "media", "assets", "p.jpg")
        Image.new("RGB", (1041, 694), (120, 90, 60)).save(png)
        e = {"id": "p", "scene": "plan", "title": "Photo", "page_url": "https://example.org/p", "author": "A", "license": "Public Domain", "kind": "photo", "status": "VERIFIED",
             "local_path": "media/assets/p.jpg", "sha256": hashlib.sha256(open(png, "rb").read()).hexdigest(), "retrieved": "2026-10-21", "attribution_text": "A", "depicts_reality": True}
        json.dump({"schema": "yt-media-ledger/1", "entries": [e]}, open(os.path.join(d, "media", "ledger.json"), "w"))
        n = json.load(open(os.path.join(d, "research", "notes.json")))
        g = {"type": "compare", "title": "T", "source": "S", "left": {"file": "media/assets/p.jpg", "label": "L", "credit": "C"}, "right": {"file": "media/assets/p.jpg", "label": "L", "credit": "C"}}
        n["infographics"] = [{"id": "i_c", "chapter": "plan", "claims": ["C2"], "graphic": g}]
        json.dump(n, open(os.path.join(d, "research", "notes.json"), "w"))
        ep, _ = pl.plan(d)
        self.assertEqual([v for c in ep["chapters"] for v in c["visuals"] if v.get("kind") == "still"], [])
        self.assertNotIn("m_p", ep["assets"])


if __name__ == "__main__":
    unittest.main()
