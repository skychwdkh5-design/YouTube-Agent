import json, os, re, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
from unittest import mock
sys.path.insert(0, os.path.dirname(__file__))
import publish as P
import release_check as R

PUB = datetime(2026, 10, 23, 12, 0, tzinfo=timezone.utc)
PUB_S = "2026-10-23T12:00:00Z"


class Base(unittest.TestCase):
    def setUp(self):
        self.lp = os.path.join(tempfile.mkdtemp(), "ledger.jsonl"); P.LEDGER = self.lp
        P.ledger_add({"event": "uploaded", "sha256": "a", "id": "ep005", "video_id": "VID"}, self.lp)
        P.ledger_add({"event": "verified", "sha256": "a", "id": "ep005", "video_id": "VID", "ok": True, "privacyStatus": "private", "publishAt": PUB_S}, self.lp)
        self.calls = []
        self.status = {"found": True, "privacyStatus": "private", "publishAt": PUB_S, "uploadStatus": "processed", "processing": "succeeded"}

    def st(self, vid, token):
        self.calls.append(vid); return dict(self.status)

    def go(self, minutes_after, dry=False):
        with mock.patch.object(R, "gh", side_effect=self.fake_gh) as g:
            self.gh = g
            return R.run(dry=dry, now=PUB + timedelta(minutes=minutes_after), token_fn=lambda: "t", status_fn=self.st)

    def fake_gh(self, *a):
        return "https://github.com/o/r/issues/77" if a[:2] == ("issue", "create") else ""

    def events(self):
        return [r["event"] for r in P.ledger_read(self.lp)]


class Release(Base):
    def test_waits_without_calling_youtube_before_the_grace_period(self):
        self.assertEqual(self.go(-60)["items"][0]["action"], "not due yet"); self.assertEqual(self.go(2)["items"][0]["action"], "not due yet")
        self.assertEqual(self.calls, [])

    def test_public_is_confirmed_once_and_never_checked_again(self):
        self.status["privacyStatus"] = "public"
        out = self.go(5)
        self.assertEqual(out["items"][0]["action"], "release_confirmed"); self.assertIn("release_confirmed", self.events())
        self.assertEqual(self.go(20)["items"], []); self.assertEqual(self.calls, ["VID"])           # second run: nothing pending, no API call

    def test_private_is_retried_and_one_issue_is_opened_at_the_third_attempt(self):
        for m in (5, 20):
            self.assertEqual(self.go(m)["items"][0]["action"], "still not public")
        self.gh.assert_not_called()
        out = self.go(35); self.assertEqual(out["items"][0]["issue"], 77)
        self.assertEqual(sum(1 for e in self.events() if e == "release_issue"), 1)
        self.go(50); self.go(65)
        self.assertEqual(sum(1 for e in self.events() if e == "release_issue"), 1)                    # never a second issue
        issue_calls = [c for c in self.gh.call_args_list if c.args[:2] == ("issue", "create")]; self.assertEqual(issue_calls, [])   # (the last two runs created none)

    def test_late_release_confirms_and_closes_the_issue(self):
        for m in (5, 20, 35):
            self.go(m)
        self.status["privacyStatus"] = "public"
        self.go(50)
        cmds = [c.args[:2] for c in self.gh.call_args_list]
        self.assertIn(("issue", "comment"), cmds); self.assertIn(("issue", "close"), cmds); self.assertIn("release_confirmed", self.events())

    def test_missing_video_opens_an_issue_immediately(self):
        self.status = {"found": False, "video_id": "VID"}
        self.assertEqual(self.go(5)["items"][0]["issue"], 77)

    def test_rescheduled_video_is_not_an_alarm(self):
        self.status["publishAt"] = "2026-10-30T12:00:00Z"
        out = self.go(5); self.assertEqual(out["items"][0]["action"], "release_rescheduled"); self.gh.assert_not_called()
        self.assertEqual(sum(1 for e in self.events() if e == "release_issue"), 0)

    def test_gives_up_48_hours_after_publish_time(self):
        self.assertTrue(self.go(48 * 60 + 5)["items"][0]["action"].startswith("abandoned")); self.assertEqual(R.awaiting(P.ledger_read(self.lp)), []); self.assertEqual(self.calls, [])

    def test_dry_run_changes_nothing(self):
        before = P.ledger_read(self.lp); self.go(35, dry=True); self.go(5, dry=True)
        self.assertEqual(P.ledger_read(self.lp), before); self.gh.assert_not_called()

    def test_private_test_videos_and_unverified_uploads_are_ignored(self):
        P.ledger_add({"event": "verified", "id": "t", "video_id": "TEST", "ok": True, "kind": "private_test", "publishAt": PUB_S}, self.lp)
        P.ledger_add({"event": "verified", "id": "u", "video_id": "BAD", "ok": False, "publishAt": PUB_S}, self.lp)
        self.assertEqual([v["video_id"] for v in R.awaiting(P.ledger_read(self.lp))], ["VID"])


class ReadOnly(unittest.TestCase):
    def test_no_write_function_is_used(self):
        src = open(os.path.join(os.path.dirname(__file__), "release_check.py")).read()
        code = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#"))
        for bad in ("resumable_upload", "set_thumbnail", "insert_caption", "build_body", "run_entry", "queue_run", "videos.update", '"PUT"', '"DELETE"', "media.py"):
            self.assertNotIn(bad, code, bad)

    def test_a_check_never_touches_uploads_even_if_they_would_blow_up(self):
        lp = os.path.join(tempfile.mkdtemp(), "l.jsonl"); P.LEDGER = lp
        P.ledger_add({"event": "verified", "id": "x", "video_id": "V", "ok": True, "publishAt": PUB_S}, lp)
        boom = mock.Mock(side_effect=AssertionError("write attempted"))
        with mock.patch.object(P, "resumable_upload", boom), mock.patch.object(P, "set_thumbnail", boom), mock.patch.object(P, "insert_caption", boom), mock.patch.object(R, "gh", return_value=""):
            R.run(now=PUB + timedelta(minutes=10), token_fn=lambda: "t", status_fn=lambda v, t: {"found": True, "privacyStatus": "public"})
        boom.assert_not_called()


class Workflow(unittest.TestCase):
    def setUp(self):
        self.t = open(os.path.join(P.ROOT, ".github", "workflows", "verify-release.yml")).read()

    def test_runs_without_a_session_and_cannot_upload(self):
        self.assertIn("schedule:", self.t); self.assertIn("*/15 * * * *", self.t); self.assertIn("workflow_dispatch", self.t)
        self.assertIn("group: youtube-publish", self.t); self.assertIn("contents: write", self.t); self.assertIn("issues: write", self.t)
        for bad in ("environment:", "queue-run", "--confirm", "media.py", "publish.py", "actions: write", "pull-requests"):
            self.assertNotIn(bad, self.t, bad)
        self.assertIn("release_check.py", self.t)

    def test_manual_runs_default_to_dry_and_inputs_never_reach_the_shell_directly(self):
        self.assertRegex(self.t, r"dry_run:\n\s+description:.*\n\s+type: boolean\n\s+default: true")
        for line in self.t.splitlines():
            if line.strip().startswith(("run:", "python3", "git ", "if ")):
                self.assertNotIn("${{ inputs.", line)


if __name__ == "__main__":
    unittest.main()
