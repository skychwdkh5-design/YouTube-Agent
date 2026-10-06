#!/usr/bin/env python3
"""Offline tests for usgs_m2m.py - no network, no credentials needed.

    python3 test_usgs_m2m.py
"""
import io, json, os, sys, unittest
from contextlib import redirect_stdout
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import usgs_m2m as u

FAKE_USER, FAKE_TOKEN, FAKE_KEY = "fake-user-xyz", "fake-token-SECRET-123", "fake-apikey-456"


def fake_api(responses):
    """Replace M2M.call so each endpoint returns a canned response."""
    calls = []

    def call(self, endpoint, payload=None, auth=True):
        calls.append((endpoint, payload))
        if endpoint == "login-token":
            assert payload == {"username": FAKE_USER, "token": FAKE_TOKEN}
            return FAKE_KEY
        if auth and not self.key:
            raise u.M2MError("not authenticated")
        r = responses.get(endpoint)
        if isinstance(r, Exception): raise r
        return r
    return call, calls


SCENE = {"entityId": "LC80150332025240LGN00", "displayId": "LC08_L1TP_015033_20250828_20250903_02_T1",
         "cloudCover": "3.1", "temporalCoverage": {"startDate": "2025-08-28 00:00:00"},
         "browse": [{"browsePath": "https://example/browse.jpg"}]}


def run(argv, responses):
    call, calls = fake_api(responses)
    env = {"USGS_M2M_USERNAME": FAKE_USER, "USGS_M2M_TOKEN": FAKE_TOKEN}
    buf = io.StringIO()
    with mock.patch.dict(os.environ, env), mock.patch.object(u.M2M, "call", call), redirect_stdout(buf):
        code = u.main(argv)
    return code, buf.getvalue(), calls


class T(unittest.TestCase):
    def assertNoSecrets(self, text):
        for s in (FAKE_USER, FAKE_TOKEN, FAKE_KEY):
            self.assertNotIn(s, text)

    def test_auth_logs_out_and_hides_secrets(self):
        code, out, calls = run(["auth"], {"logout": None})
        self.assertEqual(code, 0)
        self.assertEqual([c[0] for c in calls], ["login-token", "logout"])
        self.assertNoSecrets(out)

    def test_missing_env(self):
        buf = io.StringIO()
        with mock.patch.dict(os.environ, {"USGS_M2M_USERNAME": "", "USGS_M2M_TOKEN": ""}), redirect_stdout(buf):
            self.assertEqual(u.main(["auth"]), 2)
        self.assertIn("USGS_M2M_TOKEN", buf.getvalue())

    def test_search_point(self):
        code, out, calls = run(["search", "--point", "38.9", "-77.0", "--start", "2025-06-01",
                                "--end", "2025-08-31", "--cloud", "20"],
                               {"scene-search": {"totalHits": 1, "results": [SCENE]}})
        self.assertEqual(code, 0)
        d = json.loads(out)
        self.assertEqual(d["status"], "ok")
        self.assertEqual(d["scenes"][0]["acquired"], "2025-08-28")
        f = calls[1][1]["sceneFilter"]
        self.assertEqual(f["cloudCoverFilter"]["max"], 20)
        self.assertLess(f["spatialFilter"]["lowerLeft"]["latitude"], 38.9)

    def test_search_empty_is_reported_not_invented(self):
        code, out, _ = run(["search", "--bbox", "-1", "-1", "1", "1", "--start", "2025-01-01",
                            "--end", "2025-01-02"], {"scene-search": {"totalHits": 0, "results": []}})
        d = json.loads(out)
        self.assertEqual((code, d["status"], d["scenes"]), (0, "no_scenes", []))

    def test_bad_bbox(self):
        code, out, calls = run(["search", "--bbox", "10", "0", "5", "1", "--start", "a", "--end", "b"], {})
        self.assertEqual(code, 2); self.assertEqual(calls, [])

    def test_api_error_is_redacted(self):
        err = u.M2MError(u._redact(f"scene-search: X: bad {FAKE_TOKEN}", [FAKE_TOKEN]))
        code, out, _ = run(["search", "--bbox", "-1", "-1", "1", "1", "--start", "a", "--end", "b"],
                           {"scene-search": err})
        self.assertEqual(code, 2); self.assertNoSecrets(out)

    def test_options(self):
        code, out, _ = run(["options", "--entity", "E1"], {"download-options": [
            {"id": "p1", "productName": "Bundle", "available": True, "filesize": 1306538335}]})
        self.assertEqual(json.loads(out)["options"][0]["filesize"], 1306538335)

    def test_download_needs_confirm(self):
        code, out, calls = run(["download", "--entity", "E1", "--product", "Bundle"], {})
        self.assertEqual(code, 2); self.assertEqual(calls, [])

    def test_download_refuses_large(self):
        code, out, calls = run(["download", "--entity", "E1", "--product", "Bundle", "--confirm"],
                               {"download-options": [{"id": "p1", "productName": "Bundle",
                                                      "available": True, "filesize": 1306538335}]})
        self.assertEqual(code, 2)
        self.assertIn("max-mb", out)
        self.assertNotIn("download-request", [c[0] for c in calls])
        self.assertEqual(calls[-1][0], "logout")


if __name__ == "__main__":
    unittest.main(verbosity=1)
