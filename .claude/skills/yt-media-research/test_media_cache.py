#!/usr/bin/env python3
import hashlib, json, os, sys, tempfile, unittest
from unittest import mock
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import media as M
import media_cache as C


def mkroot(d, scene="plan"):
    os.makedirs(os.path.join(d, "research")); os.makedirs(os.path.join(d, "media", "assets"))
    open(os.path.join(d, "media", "assets", "p.jpg"), "wb").write(b"jpegdata" * 100)
    sha = hashlib.sha256(open(os.path.join(d, "media", "assets", "p.jpg"), "rb").read()).hexdigest()
    e = {"id": "p", "scene": scene, "title": "Shore", "page_url": "https://example.org/p", "author": "A", "license": "Public Domain", "kind": "photo", "status": "UNVERIFIED",
         "local_path": "media/assets/p.jpg", "sha256": sha, "retrieved": "2026-10-21", "attribution_text": "Shore / A / PD", "rights_evidence": "page says public domain, read 2026-10-21", "depicts_reality": True}
    json.dump({"schema": "yt-media-ledger/1", "entries": [e]}, open(os.path.join(d, "media", "ledger.json"), "w"))
    json.dump({"media_scenes": {scene: ["shore"], "close": ["sunset"]}}, open(os.path.join(d, "research", "notes.json"), "w"))


class Cache(unittest.TestCase):
    def setUp(self):
        self.cache = tempfile.mkdtemp()
        p = mock.patch.object(C, "CACHE", self.cache); p.start(); self.addCleanup(p.stop)

    def test_verified_entry_is_cached_and_reused_by_another_episode_offline(self):
        a = tempfile.mkdtemp(); mkroot(a)
        led = M.load(a); M.refresh(led, a); M.save(a, led)
        e = M.load(a)["entries"][0]; self.assertEqual(e["status"], "VERIFIED")
        C.put(e, a)
        b = tempfile.mkdtemp(); mkroot(b, "segment")
        led = M.load(b); led["entries"][0].update(status="DISCOVERED", local_path=None, sha256=None, rights_evidence=None, license=None); M.save(b, led)
        self.assertEqual(C.apply(b), 1)
        got = M.load(b)["entries"][0]
        self.assertEqual(got["status"], "VERIFIED"); self.assertTrue(os.path.exists(os.path.join(b, got["local_path"])))

    def test_unverified_entries_are_never_cached(self):
        a = tempfile.mkdtemp(); mkroot(a)
        with self.assertRaises(ValueError):
            C.put(M.load(a)["entries"][0], a)

    def test_tampered_cached_file_is_not_applied(self):
        a = tempfile.mkdtemp(); mkroot(a)
        led = M.load(a); M.refresh(led, a); M.save(a, led)
        c = C.put(M.load(a)["entries"][0], a)
        open(os.path.join(self.cache, c["cached_file"]), "wb").write(b"changed")
        b = tempfile.mkdtemp(); mkroot(b)
        led = M.load(b); led["entries"][0].update(status="DISCOVERED", local_path=None, sha256=None); M.save(b, led)
        self.assertEqual(C.apply(b), 0)

    def test_auto_writes_visible_exceptions_when_no_provider_is_reachable(self):
        a = tempfile.mkdtemp(); mkroot(a)
        probe = [{"source": "commons", "usable": False, "status": "BLOCKED_BY_NETWORK_POLICY"}, {"source": "usgs", "usable": True, "status": "MANUAL"}]
        with mock.patch.object(M, "probe", return_value=probe):
            s = C.auto(a, run=lambda *x, **k: None)
        self.assertEqual(s["usable_providers"], [])
        exc = json.load(open(os.path.join(a, "media", "exceptions.json")))["exceptions"]
        self.assertEqual({x["chapter"] for x in exc}, {"close"})                      # 'plan' has a verified photo, 'close' has none: the exception is on file
        self.assertIn("no provider reachable", exc[0]["reason"])

    def test_probe_is_cached_for_a_day(self):
        probe = []
        with mock.patch.object(M, "probe", return_value=probe) as pr:
            C.probe_cached(); _, cached = C.probe_cached()
        self.assertTrue(cached); self.assertEqual(pr.call_count, 1)


if __name__ == "__main__":
    unittest.main()
