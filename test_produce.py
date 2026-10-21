#!/usr/bin/env python3
import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import produce as P


class Produce(unittest.TestCase):
    def test_slug(self):
        self.assertEqual(P.slugify("NEOM The Line: what satellites show!"), "neom-the-line-what-satellites-show")

    def test_voice_budget_is_written_only_when_the_script_fits_and_is_single_use_by_hash(self):
        d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, "voice"))
        self.assertIn("no voice plan", P.grant_voice_budget(d, 6000))
        json.dump({"chars": 5280, "script_sha256": "ab" * 32}, open(os.path.join(d, "voice", "plan.json"), "w"))
        self.assertIn("over the pre-approved budget", P.grant_voice_budget(d, 5000))
        self.assertFalse(os.path.exists(os.path.join(d, "approvals", "voice.json")))          # over budget: nothing is written
        self.assertIn("written", P.grant_voice_budget(d, 6000))
        ap = json.load(open(os.path.join(d, "approvals", "voice.json")))
        self.assertTrue(ap["approved"]); self.assertEqual(ap["script_sha256"], "ab" * 32); self.assertLessEqual(ap["max_chars"], 5290)
        self.assertIn("already", P.grant_voice_budget(d, 6000))


if __name__ == "__main__":
    unittest.main()
