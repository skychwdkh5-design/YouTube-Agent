#!/usr/bin/env python3
import os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import facts as f


def C(id_, tier="media", conf="medium", **kw):
    d = {"id": id_, "tier": tier, "text": "t", "confidence": conf, "attribution": "Outlet", "date": "2026-01-01", "url": "https://x", "wording": "reported"}
    d.update(kw)
    return d


class Lint(unittest.TestCase):
    def setUp(self):
        self.cl = {c["id"]: c for c in [C("C1"), C("C2", "original", "high", wording=None), C("C3", "hypothesis", "low"),
                                         C("C4", "media", "low"), C("C5", "media", forbid=["collapsed"])]}

    def lint(self, text, **kw):
        return f.lint_script(text, self.cl, **kw)[0]

    def test_untagged_number_blocked(self):
        self.assertTrue(any("without a claim id" in p for p in self.lint("The line is 170 km long.")))

    def test_tagged_ok(self):
        self.assertEqual(self.lint("The plan was announced at 170 km. {C2}"), [])

    def test_unknown_id(self):
        self.assertTrue(any("unknown claim" in p for p in self.lint("It is 5 km. {C99}")))

    def test_media_needs_attribution_word(self):
        self.assertTrue(any("reported" in p for p in self.lint("Work stopped in 2025. {C1}")))
        self.assertEqual(self.lint("Bloomberg reported 2.4 km by 2030. {C1}"), [])

    def test_low_confidence_blocked(self):
        self.assertTrue(any("confidence low" in p for p in self.lint("Outlet reported 3 km. {C4}")))

    def test_strong_word_blocked(self):
        self.assertTrue(any("strong word" in p for p in self.lint("The images prove the plan. {C2}")))

    def test_forbidden_word(self):
        self.assertTrue(any("forbids" in p for p in self.lint("Outlet reported it collapsed in 2024. {C5}")))

    def test_hypothesis_needs_hedge(self):
        self.assertTrue(any("hedge" in p for p in self.lint("The segment is water. {C3}")))
        self.assertEqual(self.lint("The segment may be water. {C3}"), [])

    def test_limit_tag(self):
        self.assertEqual(self.lint("We cannot prove it. {L}"), [])
        self.assertTrue(any("only for limitations" in p for p in self.lint("The images prove it. {L}")))

    def test_directions_and_headings_skipped(self):
        self.assertEqual(self.lint("# Title 2026\n[ON SCREEN: 170 km]\n"), [])


class Registry(unittest.TestCase):
    def test_observation_needs_evidence_file(self):
        c = {"O1": {"id": "O1", "tier": "observation", "text": "t", "confidence": "high", "evidence": "nope.png"}}
        self.assertTrue(f.check_claims(c, tempfile.gettempdir()))
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "e.png"), "w").write("x")
            c["O1"]["evidence"] = "e.png"
            self.assertEqual(f.check_claims(c, d), [])

    def test_media_needs_source(self):
        c = {"M": {"id": "M", "tier": "media", "text": "t", "confidence": "high", "wording": "reported"}}
        self.assertTrue(f.check_claims(c))

    def test_labels(self):
        cl = {"C2": C("C2", "original", "high")}
        self.assertTrue(f.lint_labels([{"text": "170 km"}], cl))
        self.assertEqual(f.lint_labels([{"text": "170 km", "claim": "C2"}, {"text": "OCT 2026", "exempt": True}], cl), [])


if __name__ == "__main__":
    unittest.main()
