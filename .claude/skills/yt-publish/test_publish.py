import json, os, sys, tempfile, unittest
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(__file__))
import publish as P

NOW = datetime(2026, 10, 22, tzinfo=timezone.utc)


def spec(d, **kw):
    f = os.path.join(d, "v.mp4"); open(f, "wb").write(b"x" * 10)
    return {"file": f, "kind": "long", "title": "T", "description": "D", "made_for_kids": False,
            "contains_synthetic_media": False, **kw}


class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def test_flags_never_defaulted(self):
        s = spec(self.d); del s["made_for_kids"]
        self.assertRaises(P.PublishError, P.validate, s, NOW)

    def test_schedule_forces_private_and_past_rejected(self):
        b = P.build_body(spec(self.d, privacy="public", publish_at="2026-11-03T15:00:00Z"))
        self.assertEqual(b["status"]["privacyStatus"], "private")
        self.assertEqual(b["status"]["publishAt"], "2026-11-03T15:00:00Z")
        self.assertRaises(P.PublishError, P.validate, spec(self.d, publish_at="2026-01-01T00:00:00Z"), NOW)

    def test_short_gets_hashtag_and_related_link(self):
        b = P.build_body(spec(self.d, kind="short", related_long_url="https://youtu.be/abc"))
        self.assertIn("Full video: https://youtu.be/abc", b["snippet"]["description"])
        self.assertIn("#Shorts", b["snippet"]["description"])
        self.assertEqual(P.build_body(spec(self.d))["status"]["privacyStatus"], "private")

    def test_ledger_blocks_duplicate_even_if_interrupted(self):
        lp = os.path.join(self.d, "l.jsonl")
        self.assertIsNone(P.duplicate_of("h1", lp))
        P.ledger_add({"event": "started", "sha256": "h1"}, lp)
        self.assertIsNotNone(P.duplicate_of("h1", lp))
        self.assertIsNone(P.duplicate_of("h2", lp))

    def test_redact(self):
        os.environ["YT_REFRESH_TOKEN"] = "supersecret"
        self.assertNotIn("supersecret", P.redact("bad supersecret"))


if __name__ == "__main__":
    unittest.main()
