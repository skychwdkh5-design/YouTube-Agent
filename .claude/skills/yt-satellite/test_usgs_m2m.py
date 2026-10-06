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

    # --- maintenance: robustness ---------------------------------------------------------------

    OPT = {"download-options": [{"id": "p1", "productName": "Browse", "available": True,
                                 "filesize": 3_000_000}],
           "download-request": {"availableDownloads": [{"url": "https://dl.example/signed?k=abc"}]}}

    def _download(self, responses, fetch, tmp):
        with mock.patch.object(u.M2M, "_fetch", fetch):
            return run(["download", "--entity", "E1", "--product", "Browse", "--out", tmp,
                        "--max-mb", "10", "--confirm"], responses)

    def test_download_ok_reports_cleanup(self):
        fetch = lambda self, url, out, e, mb: {"path": "x.jpg", "bytes": 3}
        code, out, calls = self._download(dict(self.OPT, **{"download-order-remove": None}), fetch, "/tmp/x")
        d = json.loads(out)
        self.assertEqual((code, d["status"], d["cleanup"]["status"]), (0, "ok", "removed"))
        names = [c[0] for c in calls]
        self.assertIn("download-order-remove", names); self.assertEqual(names[-1], "logout")
        self.assertNoSecrets(out)

    def test_cleanup_failure_keeps_download_ok(self):
        fetch = lambda self, url, out, e, mb: {"path": "x.jpg", "bytes": 3}
        code, out, _ = self._download(dict(self.OPT, **{"download-order-remove": u.M2MError("boom")}),
                                      fetch, "/tmp/x")
        d = json.loads(out)
        self.assertEqual((code, d["status"], d["cleanup"]["status"]), (0, "ok", "failed"))
        self.assertEqual(d["files"][0]["path"], "x.jpg")

    def test_network_failure_is_json_and_partial_removed(self):
        import tempfile, urllib.error
        tmp = tempfile.mkdtemp()

        class Resp(io.BytesIO):
            headers = {"Content-Disposition": "attachment; filename=scene.jpg"}
            def read(self, n=-1):
                if self.tell() >= 4: raise ConnectionResetError("reset by peer")
                return super().read(4)

        def urlopen(req, timeout=None):
            if "fail-early" in req.full_url: raise urllib.error.URLError("no route")
            return Resp(b"12345678")

        for url in ("https://dl.example/signed?k=abc", "https://dl.example/fail-early"):
            resp = dict(self.OPT, **{"download-request": {"availableDownloads": [{"url": url}]},
                                     "download-order-remove": None})
            with mock.patch.object(u.urllib.request, "urlopen", urlopen):
                code, out, calls = run(["download", "--entity", "E1", "--product", "Browse",
                                        "--out", tmp, "--confirm"], resp)
            d = json.loads(out)
            self.assertEqual((code, d["status"]), (2, "error"))
            self.assertIn("file download failed", d["error"])
            self.assertNotIn("Traceback", out); self.assertNotIn(url, out)
            self.assertEqual(d["cleanup"]["status"], "removed")
            self.assertEqual(os.listdir(tmp), [])
            self.assertEqual(calls[-1][0], "logout")

    def test_oversize_stream_deletes_partial(self):
        import tempfile
        tmp = tempfile.mkdtemp()

        class Resp(io.BytesIO):
            headers = {}
        big = b"x" * (2 * 1024 * 1024)
        with mock.patch.object(u.urllib.request, "urlopen", lambda req, timeout=None: Resp(big)):
            code, out, _ = run(["download", "--entity", "E1", "--product", "Browse", "--out", tmp,
                                "--max-mb", "1", "--confirm"],
                               {"download-options": [{"id": "p1", "productName": "Browse",
                                                      "available": True, "filesize": 1}],
                                "download-request": {"availableDownloads": [{"url": "https://d/f.jpg"}]},
                                "download-order-remove": None})
        self.assertEqual(code, 2); self.assertIn("exceeded --max-mb", out)
        self.assertEqual(os.listdir(tmp), [])

    def test_invalid_numbers_are_clean_errors(self):
        base = ["--start", "2025-01-01", "--end", "2025-01-02"]
        cases = [["search", "--point", "abc", "1"] + base,
                 ["search", "--point", "1", "1", "--max", "x"] + base,
                 ["search", "--point", "1", "1", "--radius-km", "nan"] + base,
                 ["search", "--point", "1", "1", "--cloud", "150"] + base,
                 ["search", "--bbox", "a", "0", "1", "1"] + base,
                 ["search", "--point", "1"] + base,
                 ["download", "--entity", "E1", "--product", "B", "--max-mb", "x", "--confirm"]]
        for argv in cases:
            code, out, calls = run(argv, {})
            d = json.loads(out)
            self.assertEqual((code, d["status"], calls), (2, "error", []), argv)

    def test_options_empty_is_no_options(self):
        code, out, _ = run(["options", "--entity", "E1"], {"download-options": []})
        self.assertEqual((code, json.loads(out)["status"]), (0, "no_options"))
        code, out, calls = run(["download", "--entity", "E1", "--product", "B", "--confirm"],
                               {"download-options": []})
        self.assertEqual((code, json.loads(out)["status"]), (2, "no_options"))
        self.assertNotIn("download-request", [c[0] for c in calls])

    def test_coordinate_edges_refused_not_altered(self):
        base = ["--start", "2025-01-01", "--end", "2025-01-02"]
        cases = {"180th meridian": ["search", "--point", "0", "179.99", "--radius-km", "10"],
                 "pole": ["search", "--point", "89.99", "0", "--radius-km", "10"],
                 "MINLON > MAXLON": ["search", "--bbox", "170", "0", "-170", "1"],
                 "-90..90": ["search", "--point", "91", "0"],
                 "-180..180": ["search", "--point", "0", "181"]}
        for msg, argv in cases.items():
            code, out, calls = run(argv + base, {})
            self.assertEqual((code, calls), (2, []), argv)
            self.assertIn(msg, json.loads(out)["error"])
        # a box touching the edges exactly is passed through unchanged
        code, out, calls = run(["search", "--bbox", "170", "80", "180", "90"] + base,
                               {"scene-search": {"totalHits": 0, "results": []}})
        f = calls[1][1]["sceneFilter"]["spatialFilter"]
        self.assertEqual((code, f["upperRight"]), (0, {"latitude": 90.0, "longitude": 180.0}))

    def test_unexpected_exception_is_json_and_redacted(self):
        code, out, _ = run(["search", "--bbox", "-1", "-1", "1", "1", "--start", "a", "--end", "b"],
                           {"scene-search": RuntimeError(f"weird {FAKE_TOKEN}")})
        d = json.loads(out)
        self.assertEqual((code, d["status"]), (2, "error")); self.assertNoSecrets(out)


if __name__ == "__main__":
    unittest.main(verbosity=1)
