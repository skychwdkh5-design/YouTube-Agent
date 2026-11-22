"""Offline tests for the optional free-topic scout: python -m unittest discover -s tests -p 'test_free_topic_scout.py'"""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("free_topic_scout", Path(__file__).resolve().parents[1] / "tools" / "free_topic_scout.py")
scout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scout)

class TopicScoutTests(unittest.TestCase):
    def test_rss(self):
        xml = b'<rss><channel><item><title>Test &amp; check</title><link>https://example.org/a</link><pubDate>Thu, 29 Oct 2026 12:00:00 GMT</pubDate></item></channel></rss>'
        results = scout.parse_feed(xml, "https://example.org/rss")
        self.assertEqual(results[0]["title"], "Test & check")
        self.assertEqual(results[0]["verification"], "SOURCE_REVIEW_REQUIRED")

    def test_unsafe_url_rejected(self):
        xml = b'<rss><channel><item><title>Bad</title><link>http://example.org/a</link></item></channel></rss>'
        self.assertEqual(scout.parse_feed(xml, "https://example.org/rss"), [])

    def test_date_sort(self):
        older = {"published":"Wed, 28 Oct 2026 12:00:00 GMT"}
        newer = {"published":"Thu, 29 Oct 2026 12:00:00 GMT"}
        self.assertGreater(scout.date_sort(newer), scout.date_sort(older))

if __name__ == "__main__":
    unittest.main()
