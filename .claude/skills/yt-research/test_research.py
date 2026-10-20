#!/usr/bin/env python3
import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import research as r


def note(**k):
    n = {"id": "N1", "kind": "media", "statement": "Outlet reported X.", "short": "Outlet reported X", "independent_outlets": 2,
         "source": {"outlet": "Out", "url": "https://x", "date": "2026-01-01", "access": "read", "kind": "secondary"}}
    n.update(k)
    return n


class Derive(unittest.TestCase):
    def test_confidence_is_derived(self):
        self.assertEqual(r.derive(note())[0], "medium")
        self.assertEqual(r.derive(note(independent_outlets=1))[0], "low")
        self.assertEqual(r.derive(note(source={**note()["source"], "kind": "primary"}))[0], "high")
        self.assertEqual(r.derive(note(source={**note()["source"], "access": "summary_only", "kind": "search_summary"}))[0], "medium")
        self.assertEqual(r.derive(note(source={**note()["source"], "access": "summary_only", "kind": "search_summary"}, independent_outlets=1))[0], "low")
        self.assertEqual(r.derive(note(source={**note()["source"], "access": "unreachable"}))[0], "low")
        self.assertEqual(r.derive({"kind": "observation", "basis": "two_checks"})[0], "high")
        self.assertEqual(r.derive({"kind": "hypothesis"})[0], "low")

    def test_validation(self):
        self.assertTrue(r.validate_note(note(short="x" * 50)))
        self.assertTrue(r.validate_note({"id": "O", "kind": "observation", "statement": "s", "short": "s"}))
        bad = note(); del bad["source"]["date"]
        self.assertTrue(r.validate_note(bad))
        self.assertEqual(r.validate_note(note()), [])


class Build(unittest.TestCase):
    def test_build_and_capacity_and_gaps(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "research"))
            notes = [note(), note(id="N2", independent_outlets=1), {"id": "N3", "kind": "hypothesis", "statement": "It may be water.", "short": "May be water"}]
            json.dump({"notes": notes}, open(os.path.join(d, "research", "notes.json"), "w"))
            res = r.build(d)
            c = json.load(open(os.path.join(d, "claims.json")))
            self.assertEqual(c["schema"], "yt-facts/1")
            self.assertEqual({x["id"]: x["confidence"] for x in c["claims"]}, {"N1": "medium", "N2": "low", "N3": "low"})
            self.assertEqual(c["claims"][0]["wording"], "reported")
            self.assertEqual(res["usable"], 1)
            self.assertTrue(res["insufficient_for_6_min"])
            self.assertTrue(any("N2" in g for g in res["low_claims"]))
            self.assertIn("INSUFFICIENT_FOR_6_MIN", open(os.path.join(d, "research", "report.md")).read())

    def test_invalid_notes_stop_the_build(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "research"))
            json.dump({"notes": [note(short="x" * 60)]}, open(os.path.join(d, "research", "notes.json"), "w"))
            with self.assertRaises(r.ResearchError):
                r.build(d)
            self.assertFalse(os.path.exists(os.path.join(d, "claims.json")))


class Fetch(unittest.TestCase):
    def test_unreachable_is_logged_not_substituted(self):
        with tempfile.TemporaryDirectory() as d:
            e = r.fetch(d, "https://localhost:9/none", timeout=3)
            self.assertNotEqual(e["status"], "ok")
            self.assertEqual(e["text"], "")
            lines = open(os.path.join(d, "research", "provenance.jsonl")).read().strip().splitlines()
            self.assertEqual(json.loads(lines[0])["url"], "https://localhost:9/none")

    def test_add_note_rejects_duplicates(self):
        with tempfile.TemporaryDirectory() as d:
            r.add_note(d, note())
            with self.assertRaises(r.ResearchError):
                r.add_note(d, note())


if __name__ == "__main__":
    unittest.main()
