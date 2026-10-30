#!/usr/bin/env python3
"""Offline tests for episode_report.py."""
import io, json, os, sys, tempfile, unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import episode_report as R


def ep(name, ctr=5.0, r30=65.0, as_of="2026-11-09", pub="2026-11-02", dur=450, impr=20000, views=1500, browse=12000):
    return {"episode": name, "published": pub, "as_of": as_of, "duration_s": dur, "impressions": impr, "views": views,
            "ctr_pct": ctr, "retention_30s_pct": r30, "avg_view_duration_s": 150, "avg_pct_viewed": 33,
            "traffic": {"browse": {"impressions": browse, "ctr_pct": 4.0}, "search": {"impressions": 20000 - browse, "ctr_pct": 7.0}}}


HIST = [ep("EP1", 4.0, 60.0), ep("EP2", 4.2, 62.0), ep("EP3", 4.4, 61.0),
        ep("OLD", 9.0, 90.0, as_of="2026-12-30")]          # 58 days old: not comparable to a day-7 snapshot


class Build(unittest.TestCase):
    def test_age_matched_comparison_and_hypotheses(self):
        cur = ep("EP4", 5.5, 71.0)
        cur["hypotheses"] = [{"id": "H1", "statement": "subject in 3 s", "metric": "retention_30s_pct", "direction": "higher"},
                             {"id": "H2", "statement": "cover lowers CTR", "metric": "ctr_pct", "direction": "lower"},
                             {"id": "H3", "statement": "tiny change", "metric": "avg_pct_viewed", "direction": "higher"}]
        r = R.build(cur, HIST)
        self.assertEqual(r["comparable_episodes"], ["EP1", "EP2", "EP3"])
        res = {h["id"]: h["result"] for h in r["hypotheses"]}
        self.assertEqual(res, {"H1": "supported", "H2": "not supported", "H3": "inconclusive"})
        self.assertIn("correlation", r["_note"])

    def test_small_sample_inconclusive(self):
        cur = ep("EP4", 9.0, impr=300, views=40)
        cur["hypotheses"] = [{"id": "H", "statement": "s", "metric": "ctr_pct", "direction": "higher"}]
        self.assertEqual(R.build(cur, HIST)["hypotheses"][0]["result"], "inconclusive")

    def test_confounders(self):
        r = R.build(ep("EP4", dur=900, browse=2000), HIST)
        self.assertTrue(any("duration" in n and "traffic mix" in n for n in r["confounders"]))

    def test_retention_curve(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.csv")
            with open(p, "w") as f:
                f.write("pos,pct\n" + "\n".join(f"{x},{y}" for x, y in
                        [(0, 100), (5, 90), (10, 80), (20, 75), (30, 70), (40, 69), (50, 60), (60, 59), (70, 62), (80, 58), (90, 57)]))
            c = R.retention_curve(p, None)            # positions in seconds
        self.assertEqual(c["dips"][0]["drop_pts"], 9.0)
        self.assertEqual(c["at_30s_pct"], 70.0)

    def test_markdown_questions_and_cli(self):
        with tempfile.TemporaryDirectory() as d:
            m, h = os.path.join(d, "m.json"), os.path.join(d, "h.jsonl")
            with open(m, "w") as f: json.dump(ep("EP4"), f)
            with open(h, "w") as f: f.write("\n".join(json.dumps(x) for x in HIST) + "\n")
            buf = io.StringIO()
            with redirect_stdout(buf): code = R.main([m, "--history", h, "--markdown", "--append"])
            out = buf.getvalue()
            self.assertEqual(code, 0)
            for q in ("Which assumptions held?", "Which did not?", "Where did viewers leave?", "What to test next", "not causation"):
                self.assertIn(q, out)
            with open(h) as f: self.assertEqual(len(f.read().splitlines()), 5)
            with redirect_stdout(io.StringIO()): self.assertEqual(R.main([m, "--append"]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=1)
