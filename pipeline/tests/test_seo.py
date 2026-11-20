import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import seo

GOOD = {
    "title": "600 Years of Computing Failed. 10 Hours Found This Star.",
    "search_queries": ["pulsar discovery NASA Fermi", "lattice algorithm pulsar", "how are pulsars found"],
    "description": "A code-breaking trick found a hidden pulsar in NASA Fermi data in 10 hours.\n\n"
                   "0:00 Intro\n0:20 What a pulsar is\n1:42 The trick\n\nSources: https://science.nasa.gov/x\n\n#Pulsar #NASA #Fermi",
    "tags": ["pulsar discovery NASA Fermi", "pulsar", "NASA Fermi", "neutron star", "lattice algorithm", "gamma rays",
             "open science", "NEXORA"],
}


def by(res):
    return {n: ok for n, ok, _ in res}


class SeoTest(unittest.TestCase):
    def test_good_passes(self):
        r = by(seo.check(GOOD, "NEXORA", duration=221.6))
        self.assertTrue(all(r.values()), r)

    def test_missing_queries_and_hashtags_fail(self):
        m = dict(GOOD, search_queries=["pulsar"], description=GOOD["description"].replace("#Pulsar #NASA #Fermi", "#NEXORA"))
        r = by(seo.check(m, "NEXORA"))
        self.assertFalse(r["seo: 3 search queries"])
        self.assertFalse(r["seo: hashtags"])

    def test_hook_needs_query_words_and_no_link(self):
        m = dict(GOOD, description="https://x.y Watch this amazing video today.\n" + GOOD["description"])
        self.assertFalse(by(seo.check(m, "NEXORA"))["seo: description hook"])

    def test_chapters_rules(self):
        m = dict(GOOD, description=GOOD["description"].replace("0:00 Intro", "0:05 Intro"))
        self.assertFalse(by(seo.check(m, "NEXORA"))["seo: chapters"])

    def test_tags_need_channel_and_count(self):
        m = dict(GOOD, tags=GOOD["tags"][:-1])
        self.assertFalse(by(seo.check(m, "NEXORA"))["seo: tags"])


if __name__ == "__main__":
    unittest.main()
