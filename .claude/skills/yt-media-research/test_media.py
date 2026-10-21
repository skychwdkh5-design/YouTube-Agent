#!/usr/bin/env python3
"""Tests use CANNED API payloads in the documented shapes of each provider (parsing + rights rules). They prove the code, not that a library is reachable:
reachability is measured live by `media.py probe` and reported as BLOCKED when the network policy denies it."""
import json, os, sys, tempfile, unittest, io, contextlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import media as m

COMMONS = {"query": {"pages": {"1": {"title": "File:Salton Sea shore.jpg", "imageinfo": [{"url": "https://upload.wikimedia.org/x.jpg", "descriptionurl": "https://commons.wikimedia.org/wiki/File:Salton_Sea_shore.jpg",
           "width": 4000, "height": 3000, "mime": "image/jpeg", "extmetadata": {"LicenseShortName": {"value": "CC BY 4.0"}, "Artist": {"value": "<a href='x'>Jane Roe</a>"}, "AttributionRequired": {"value": "true"},
           "Copyrighted": {"value": "True"}, "UsageTerms": {"value": "Creative Commons Attribution 4.0"}}}]},
    "2": {"title": "File:Salton Sea sa.jpg", "imageinfo": [{"url": "u", "descriptionurl": "https://commons.wikimedia.org/wiki/File:Sa.jpg", "mime": "image/jpeg", "extmetadata": {"LicenseShortName": {"value": "CC BY-SA 3.0"}, "Artist": {"value": "A"}}}]}}}}
NASA = {"collection": {"items": [{"data": [{"nasa_id": "PIA00001", "title": "Salton Sea", "center": "JPL", "date_created": "2015-10-09T00:00:00Z", "media_type": "image", "description": "<b>x</b>"}],
        "links": [{"href": "https://images-assets.nasa.gov/p.jpg", "render": "image"}]}]}}


def entry(**k):
    e = {"id": "a", "scene": "shows", "title": "t", "page_url": "https://example.org/p", "author": "A. Author", "license": "Public Domain", "kind": "photo", "rights_evidence": "read on the file page 2026-10-21",
         "local_path": "media/assets/a.jpg", "sha256": "0" * 64}
    e.update(k); return e


class Rules(unittest.TestCase):
    def test_license_classes(self):
        for lic, cls in (("CC0 1.0", "PUBLIC_DOMAIN"), ("Public domain", "PUBLIC_DOMAIN"), ("CC BY 4.0", "CC_BY"), ("CC BY-SA 3.0", "CC_BY_SA"), ("CC BY-NC 2.0", "CC_RESTRICTED"),
                         ("CC BY-ND 4.0", "CC_RESTRICTED"), ("All rights reserved", "COPYRIGHTED"), ("Pexels License", "FREE_LICENSE_PEXELS"), ("Unsplash License", "FREE_LICENSE_UNSPLASH"),
                         ("Pixabay Content License", "FREE_LICENSE_PIXABAY"), ("USGS public domain", "US_GOVERNMENT"), ("NASA media usage guidelines (not copyrighted)", "US_GOVERNMENT"), ("", "UNKNOWN"), ("custom", "UNKNOWN")):
            self.assertEqual(m.classify(lic)["class"], cls, lic)

    def test_verified_needs_everything(self):
        self.assertEqual(m.evaluate(entry())[0], "VERIFIED")
        self.assertEqual(m.evaluate(entry(rights_evidence=None))[0], "DISCOVERED")        # found, licence never read: not evidence
        self.assertEqual(m.evaluate(entry(local_path=None))[0], "UNVERIFIED")
        self.assertEqual(m.evaluate(entry(sha256=None))[0], "UNVERIFIED")
        self.assertEqual(m.evaluate(entry(author=""))[0], "UNVERIFIED")
        self.assertEqual(m.evaluate(entry(page_url="http://x"))[0], "UNVERIFIED")

    def test_attribution_and_share_alike_and_rejections(self):
        self.assertEqual(m.evaluate(entry(license="CC BY 4.0"))[0], "UNVERIFIED")                          # attribution text missing
        self.assertEqual(m.evaluate(entry(license="CC BY 4.0", attribution_text="x / y / CC BY 4.0"))[0], "VERIFIED")
        self.assertEqual(m.evaluate(entry(license="CC BY-SA 3.0", attribution_text="x"))[0], "NEEDS_OWNER")
        for lic in ("CC BY-NC 4.0", "CC BY-ND 4.0", "All rights reserved", "© Getty Images"):
            self.assertEqual(m.evaluate(entry(license=lic))[0], "REJECTED", lic)

    def test_renderings_are_never_unlabelled_stand_ins_for_photos(self):
        st, why = m.evaluate(entry(kind="rendering"))
        self.assertNotEqual(st, "VERIFIED")
        self.assertTrue(any("label" in w for w in why))
        self.assertEqual(m.evaluate(entry(kind="rendering", on_screen_label="ARTIST'S RENDERING"))[0], "VERIFIED")

    def test_web_search_alone_is_not_a_licence(self):
        e = entry(rights_evidence=None, discovered_by="web-search", local_path=None, sha256=None)
        self.assertEqual(m.evaluate(e)[0], "DISCOVERED")


class Providers(unittest.TestCase):
    def test_commons_parse(self):
        r = m.parse_commons(COMMONS)
        by = {x["title"]: x for x in r}
        a = by["Salton Sea shore.jpg"]
        self.assertEqual((a["license"], a["author"], a["attribution_required"]), ("CC BY 4.0", "Jane Roe", True))
        self.assertIn("LicenseShortName='CC BY 4.0'", a["rights_evidence"])
        self.assertEqual(m.evaluate(dict(a, id="c", scene="s", kind="photo", attribution_text="x", local_path="p", sha256="0" * 64))[0], "VERIFIED")
        sa = by["Salton Sea sa.jpg"]
        self.assertEqual(m.evaluate(dict(sa, id="d", scene="s", attribution_text="x", local_path="p", sha256="0" * 64))[0], "NEEDS_OWNER")

    def test_nasa_parse(self):
        r = m.parse_nasa(NASA)[0]
        self.assertEqual((r["nasa_id"], r["author"]), ("PIA00001", "JPL"))
        self.assertEqual(m.classify(r["license"])["class"], "US_GOVERNMENT")
        self.assertEqual(r["description"], "x")

    def test_key_providers_parse(self):
        self.assertEqual(m.parse_pexels({"photos": [{"id": 1, "url": "https://www.pexels.com/photo/1/", "photographer": "P", "src": {"original": "https://images.pexels.com/1.jpg"}, "alt": "desert"}]})[0]["license"], "Pexels License")
        self.assertEqual(m.parse_pixabay({"hits": [{"pageURL": "https://pixabay.com/photos/x-1/", "user": "U", "largeImageURL": "https://pixabay.com/1.jpg", "tags": "desert"}]})[0]["license"], "Pixabay Content License")
        self.assertEqual(m.parse_unsplash({"results": [{"id": "z", "links": {"html": "https://unsplash.com/photos/z"}, "urls": {"full": "https://images.unsplash.com/z"}, "user": {"name": "N"}}]})[0]["license"], "Unsplash License")

    def test_missing_key_is_reported_not_guessed(self):
        for k in ("PEXELS_API_KEY",):
            os.environ.pop(k, None)
        r = m.search("pexels", "desert")
        self.assertEqual((r["status"], r["results"]), ("NEEDS_API_KEY", []))

    def test_blocked_network_is_reported_as_blocked(self):
        orig = m.http_json
        m.http_json = lambda *a, **k: (_ for _ in ()).throw(OSError("Tunnel connection failed: 403 Forbidden"))
        try:
            r = m.search("commons", "x")
        finally:
            m.http_json = orig
        self.assertEqual((r["status"], r["results"]), ("BLOCKED", []))


class Cli(unittest.TestCase):
    def run_cli(self, *a):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = m.main(list(a))
        return code, json.loads(buf.getvalue())

    def test_add_verify_fetch_gate(self):
        d = tempfile.mkdtemp()
        c, out = self.run_cli("add", "--root", d, "--scene", "shows", "--page-url", "https://commons.wikimedia.org/wiki/File:X.jpg", "--title", "X", "--author", "Jane", "--license", "CC BY 4.0",
                              "--attribution-text", "X / Jane / CC BY 4.0", "--rights-evidence", "read 2026-10-21", "--kind", "photo", "--file-url", "https://upload.wikimedia.org/x.jpg")
        self.assertEqual(out["status"], "UNVERIFIED")                                  # rights fine, file not fetched: not yet VERIFIED
        c, res = self.run_cli("fetch", "--root", d)                                    # without --confirm nothing is downloaded
        self.assertIn("would_fetch", res[0])
        c, out = self.run_cli("add", "--root", d, "--scene", "shows", "--page-url", "https://example.org/b", "--title", "B", "--author", "A", "--license", "All rights reserved", "--kind", "photo")
        self.assertEqual(out["status"], "REJECTED")
        c, res = self.run_cli("fetch", "--root", d, "--id", out["id"], "--confirm")
        self.assertIn("skipped", res[0])                                               # a rejected entry is never downloaded
        c, g = self.run_cli("gaps", "--root", d)
        self.assertEqual(g["shows"]["verified"], [])


if __name__ == "__main__":
    unittest.main()
