import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout
from unittest import mock

sys.path.insert(0, os.path.dirname(__file__))
import ci_ask  # noqa: E402
import control  # noqa: E402

NX_LOG = """now 2026-11-21 03:10Z
  21.11 08:00 ICT  ep004-chips@v1            -70XeSSj9bI  due
  22.11 08:00 ICT  ep005-x@v1                abcdEFGH123  upcoming
  21.11 06:00 ICT  ai-bubble@v1              MFzEK6StU3s  due
queue: 1 upcoming
  ep004-chips@v1: private 70 min after publishAt -> issue
  ai-bubble@v1: public (confirmed, 3 min after publishAt)
"""


class Scanners(unittest.TestCase):
    def test_auth(self):
        self.assertIsNotNone(ci_ask.scan_auth_text('{"error": "token refresh failed: invalid_grant"}'))
        self.assertIsNotNone(ci_ask.scan_auth_text("NEXORA_YT_REFRESH_TOKEN is not set"))
        self.assertIsNone(ci_ask.scan_auth_text('{"error": "quotaExceeded"}'))
        self.assertIsNone(ci_ask.scan_auth_text("HTTP 500 backendError"))

    def test_yt_release(self):
        data = {"items": [
            {"id": "EP015", "video_id": "abc123XYZ_-", "publishAt": "2026-11-21T12:00:00Z", "action": "still not public",
             "attempt": 4, "privacyStatus": "private", "found": True, "issue": 77},
            {"id": "EP014", "video_id": "x", "action": "still not public", "attempt": 1, "privacyStatus": "private"},
            {"id": "EP013", "video_id": "y", "action": "release_confirmed"},
            {"id": "EP012", "action": "not due yet"}]}
        asks, res = ci_ask.scan_yt_release(data)
        self.assertEqual([a["dedup_key"] for a in asks], ["OrbitalAtlas/release/EP015"])   # no issue yet -> silent
        self.assertEqual(res, ["OrbitalAtlas/release/EP013"])
        self.assertTrue(asks[0]["link"].startswith("https://studio.youtube.com/video/abc123XYZ_-"))
        self.assertEqual(control.gate(asks[0]), (True, "ok"))

    def test_nx_release(self):
        asks, res = ci_ask.scan_nx_release(NX_LOG)
        self.assertEqual([a["dedup_key"] for a in asks], ["NEXORA/release/ep004-chips@v1"])
        self.assertIn("21.11 08:00 ICT", asks[0]["need"])
        self.assertIn("-70XeSSj9bI", asks[0]["link"])
        self.assertEqual(res, ["NEXORA/release/ai-bubble@v1"])
        self.assertEqual(control.gate(asks[0]), (True, "ok"))

    def test_pipeline_only_auth_reaches_owner(self):
        self.assertEqual(ci_ask.scan_pipeline([{"ok": False, "error_kind": "quota"}, {"ok": False, "error_kind": "error"},
                                               {"ok": True}]), [])
        a = ci_ask.scan_pipeline([{"ok": False, "error_kind": "auth", "error": "invalid_grant"}])
        self.assertEqual(a[0]["dedup_key"], "OrbitalAtlas/youtube-oauth")
        self.assertEqual(control.gate(a[0]), (True, "ok"))


class NeverFails(unittest.TestCase):
    def test_exit_zero_even_on_crash(self):
        with mock.patch.object(ci_ask, "execute", side_effect=RuntimeError("boom")), redirect_stdout(io.StringIO()) as b:
            self.assertEqual(ci_ask.main(["resolve", "--dedup", "x"]), 0)
        self.assertIn('"ok": false', b.getvalue())

    def test_silent_when_nothing(self):
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "", "GH_TOKEN": "", "GITHUB_REPOSITORY": ""}), \
             redirect_stdout(io.StringIO()) as b:
            self.assertEqual(ci_ask.main(["scan-pipeline", "/nonexistent"]), 0)
        self.assertIn("silent", b.getvalue())

    def test_missing_telegram_secrets_queue_not_lose(self):
        env = {"GITHUB_TOKEN": "", "GH_TOKEN": "", "GITHUB_REPOSITORY": "", "TELEGRAM_BOT_TOKEN": "", "TELEGRAM_CHAT_ID": ""}
        with mock.patch.dict(os.environ, env), redirect_stdout(io.StringIO()) as b:
            ci_ask.main(["scan-pipeline", "/nonexistent"])
            res = ci_ask.execute(ci_ask.scan_pipeline([{"ok": False, "error_kind": "auth", "error": "invalid_grant"}]), [], "t")
        self.assertTrue(res["asks"][0]["queued_for_retry"])


class Extras(unittest.TestCase):
    ENV = {"GITHUB_TOKEN": "", "GH_TOKEN": "", "GITHUB_REPOSITORY": "", "TELEGRAM_BOT_TOKEN": "", "TELEGRAM_CHAT_ID": ""}

    def test_check_without_secrets(self):
        with mock.patch.dict(os.environ, self.ENV):
            r = ci_ask.check()
        self.assertFalse(r["ok"]); self.assertFalse(r["bot_token_present"])

    def test_from_file_resolve_and_ask(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"op": "resolve", "dedup_key": "OrbitalAtlas/card/x"}, f)
        with mock.patch.dict(os.environ, self.ENV), redirect_stdout(io.StringIO()) as b:
            self.assertEqual(ci_ask.main(["from-file", f.name]), 0)
        os.unlink(f.name)
        self.assertIn('"ok": true', b.getvalue())

    def test_remind_dispatched_only_after_real_ask(self):
        with mock.patch.dict(os.environ, self.ENV), mock.patch.object(ci_ask, "dispatch_remind", return_value=True) as d, \
             redirect_stdout(io.StringIO()):
            ci_ask.execute([], ["k"], "t")
            d.assert_not_called()
            ci_ask.execute(ci_ask.scan_pipeline([{"ok": False, "error_kind": "auth", "error": "invalid_grant"}]), [], "t")
            d.assert_called_once()


if __name__ == "__main__":
    unittest.main()
