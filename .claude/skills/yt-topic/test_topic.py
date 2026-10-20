#!/usr/bin/env python3
import json, os, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import topic as t
KB = os.path.join(HERE, "..", "..", "..", "docs", "knowledge", "ep005-neom", "data")


def vids(n, **kw):
    return [dict({"views": 300000, "subs": 30000, "age_days": 20, "channel": f"c{i}"}, **kw) for i in range(n)]


RATE = {k: 3 for k in t.RATED}
WHY = {k: "a written rationale" for k in t.RATED}


def cand(id_, ratings=None, videos=None, img=None, **kw):
    return {"id": id_, "ratings": ratings or dict(RATE), "rationale": WHY, "videos": vids(8) if videos is None else videos,
            "imagery": img or {"years_wanted": [2020, 2022], "years_found": [2020, 2022], "years_missing": []}, **kw}


class Parse(unittest.TestCase):
    def test_age(self):
        self.assertEqual(t.age_days("2w ago"), 14)
        self.assertEqual(t.age_days("Streamed 1mo ago"), 30)
        self.assertIsNone(t.age_days("live"))

    def test_n(self):
        self.assertEqual(t.parse_n("1.5M views"), 1500000)
        self.assertEqual(t.parse_n("274K"), 274000)


class Score(unittest.TestCase):
    def test_missing_ratings_not_guessed(self):
        c = cand("x"); c["ratings"] = {"us": 4}
        r = t.score_candidate(c)
        self.assertEqual(r["status"], "needs_data")
        self.assertIn("rating:visual", r["missing"])

    def test_short_rationale_blocks(self):
        c = cand("x"); c["rationale"] = dict(WHY, us="x")
        self.assertIn("rationale:us", t.score_candidate(c)["missing"])

    def test_no_videos_no_demand(self):
        self.assertIn("data:demand", t.score_candidate(cand("x", videos=[]))["missing"])

    def test_imagery_unchecked_blocks(self):
        c = cand("x"); c["imagery"] = None
        self.assertIn("data:imagery", t.score_candidate(c)["missing"])

    def test_evidence_gate(self):
        r = t.score_candidate(cand("x", ratings=dict(RATE, evidence=2)))
        self.assertEqual(r["status"], "disqualified")

    def test_no_scene_gate(self):
        r = t.score_candidate(cand("x", img={"years_wanted": [2020], "years_found": [], "years_missing": [2020]}))
        self.assertEqual(r["status"], "disqualified")

    def test_us_dominates_scandinavia(self):
        a = cand("us_topic", ratings=dict(RATE, us=5, se=1, no=1, dk=1))
        b = cand("nordic_topic", ratings=dict(RATE, us=3, se=5, no=5, dk=5))
        r = t.rank([a, b])
        self.assertEqual(r["chosen"], "us_topic")

    def test_scandinavia_breaks_ties(self):
        a = cand("a", ratings=dict(RATE, se=1, no=1, dk=1)); b = cand("b", ratings=dict(RATE, se=5, no=5, dk=5))
        self.assertEqual(t.rank([a, b])["chosen"], "b")

    def test_satellite_not_required(self):
        c = cand("x", needs_satellite=False); c["imagery"] = None
        self.assertEqual(t.score_candidate(c)["status"], "ok")


class RealData(unittest.TestCase):
    """EP005 data: measured demand for NEOM / Aral / Salton from the saved collection."""
    def test_demand_from_saved_neom_data(self):
        rows = json.load(open(os.path.join(KB, "neom_videos_all.json")))
        v = [{"views": r["views"], "subs": r["subs_n"], "age_days": t.age_days(r["age"])} for r in rows]
        pts, facts = t.demand(v)
        self.assertGreaterEqual(pts, 3.0)
        self.assertGreater(facts["recent_small_hits"], 0)

    def test_demand_aral_is_lower_than_neom(self):
        alt = json.load(open(os.path.join(KB, "alt_topics.json")))
        neom = json.load(open(os.path.join(KB, "neom_videos_all.json")))
        f = lambda rows, sk: [{"views": r["views"], "subs": r.get(sk), "age_days": t.age_days(r["age"])} for r in rows]
        a, _ = t.demand(f(alt["aral"], "subs_n"))
        n, _ = t.demand(f(neom, "subs_n"))
        self.assertLess(a, n)


if __name__ == "__main__":
    unittest.main()
