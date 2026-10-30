#!/usr/bin/env python3
"""Offline tests for topic_score.py."""
import io, json, os, sys, tempfile, unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import topic_score as T

FULL = {k: 4 for k in T.CRITERIA}
EV = {k: "source" for k in T.CRITERIA}


def topic(i, **over):
    s = dict(FULL); s.update(over)
    return {"id": i, "title": i, "scores": s, "evidence": EV}


class Rank(unittest.TestCase):
    def test_go_and_gates(self):
        rows = {r["id"]: r for r in T.rank([topic("ok"), topic("norights", rights=2), topic("long", length_fit=2),
                                            topic("weak", us_interest=2, novelty=2, hook=2, thumbnail=2, proof=2)])}
        self.assertEqual(rows["ok"]["status"], "GO-CANDIDATE")
        self.assertEqual((rows["norights"]["status"], rows["norights"]["blocked_by"]), ("BLOCKED", ["rights"]))
        self.assertEqual(rows["long"]["blocked_by"], ["length_fit"])
        self.assertEqual(rows["weak"]["status"], "HOLD")

    def test_competitor_views_alone_never_choose(self):
        t = topic("copy", **{k: 3 for k in T.CRITERIA if k != "proof"}, proof=5)
        self.assertEqual(T.rank([t])[0]["status"], "HOLD (competitor-only)")

    def test_proof_weight_is_lowest(self):
        self.assertEqual(min(T.CRITERIA.values()), T.CRITERIA["proof"])

    def test_missing_evidence_reported_and_validation(self):
        t = topic("x"); t["evidence"] = {"facts": "nasa"}
        self.assertIn("rights", T.rank([t])[0]["missing_evidence"])
        with self.assertRaises(ValueError): T.score({"id": "m", "scores": {"facts": 3}})
        with self.assertRaises(ValueError): T.score(topic("r", hook=7))

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "t.json")
            with open(p, "w") as f: json.dump({"topics": [topic("a")]}, f)
            buf = io.StringIO()
            with redirect_stdout(buf): code = T.main([p, "--markdown"])
            self.assertEqual(code, 0); self.assertIn("GO-CANDIDATE", buf.getvalue())
            with redirect_stdout(io.StringIO()): self.assertEqual(T.main([os.path.join(d, "no.json")]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=1)
