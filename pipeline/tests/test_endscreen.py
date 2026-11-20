import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import endscreen

V = [{"video_id": "a", "privacy": "public", "seconds": 263, "publishedAt": "2026-11-20T01:00:00Z", "title": "NASA Watched the Pacific Turn Red"},
     {"video_id": "b", "privacy": "public", "seconds": 393, "publishedAt": "2026-11-16T01:00:00Z", "title": "SpaceX Caught Starship From Orbit"},
     {"video_id": "c", "privacy": "private", "seconds": 22, "publishedAt": "2026-11-21T01:00:00Z", "title": None},
     {"video_id": "d", "privacy": "public", "seconds": 40, "publishedAt": "2026-11-21T02:00:00Z", "title": "Starship short"}]


class EndscreenTest(unittest.TestCase):
    def test_related_topic_wins(self):
        r = endscreen.pick(V, "Starship Flight 12 Lands", ["Starship"])
        self.assertEqual(r["video_id"], "b")
        self.assertEqual(r["why"], "related topic")

    def test_newest_public_long_when_unrelated(self):
        r = endscreen.pick(V, "Glacier in Alaska")
        self.assertEqual(r["video_id"], "a")

    def test_excludes_self_private_and_shorts(self):
        r = endscreen.pick(V, "Pacific red", exclude={"a"})
        self.assertNotIn(r["video_id"], {"a", "c", "d"})

    def test_none_when_empty(self):
        self.assertIsNone(endscreen.pick([], "x"))


if __name__ == "__main__":
    unittest.main()
