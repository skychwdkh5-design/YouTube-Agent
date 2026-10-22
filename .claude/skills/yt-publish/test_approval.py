import argparse, copy, json, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
from unittest import mock
sys.path.insert(0, os.path.dirname(__file__))
import approval as A
import publish as P

NOW = datetime(2026, 10, 24, 5, 0, tzinfo=timezone.utc)
WHEN = "2026-10-25T12:00:00Z"                  # 19:00 Vietnam, ~31 h ahead
QUOTE = "Одобряю EP006, публикуй завтра в 19:00"


class Base(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.lp = os.path.join(self.d, "ledger.jsonl"); P.LEDGER = self.lp
        for n, b in (("thumb.jpg", b"\xff\xd8\xffthumb"), ("cap.srt", b"1\n00:00:00,000 --> 00:00:01,000\nhi\n"), ("EP006.mp4", b"video-bytes")):
            with open(os.path.join(self.d, n), "wb") as f:
                f.write(b)
        self.e = {"id": "EP006", "kind": "long", "mode": "approval", "title": "A Title", "title_status": "final", "description": "Desc",
                  "tags": ["a"], "category_id": "27", "default_language": "en", "made_for_kids": False, "contains_synthetic_media": False,
                  "media": {"asset": "EP006.mp4", "sha256": A.sha_file(os.path.join(self.d, "EP006.mp4")), "seconds": 400.0},
                  "thumbnail": "thumb.jpg", "captions": {"file": "cap.srt", "language": "en", "name": "English"}, "related": None, "publish_at": WHEN}
        self.e["thumbnail_review"] = {"result": "PASS", "sha256": A.sha_file(os.path.join(self.d, "thumb.jpg"))}
        self.manifest = {"files": [{"asset": "EP006.mp4", "sha256": self.e["media"]["sha256"], "size": 11}]}

    def record(self, **kw):
        r = A.make_record([self.e], "EP006", kw.pop("quote", QUOTE), kw.pop("scope", "single_release"), "abc123", self.d, now=NOW)
        r.update(kw); return r

    def verify(self, rec, entries=None, ledger=(), now=NOW, manifest=None):
        return A.verify_record(rec, entries or [self.e], manifest or self.manifest, self.d, list(ledger), now)


class Binding(Base):
    def test_good_approval_passes(self):
        self.assertEqual(self.verify(self.record()), [])

    def test_any_change_after_approval_voids_it(self):
        rec = self.record()
        for k, v in (("title", "Another"), ("description", "Desc 2"), ("tags", ["b"]), ("made_for_kids", True), ("contains_synthetic_media", True), ("publish_at", "2026-10-26T12:00:00Z")):
            e = copy.deepcopy(self.e); e[k] = v
            self.assertTrue(self.verify(rec, [e]), k)
        e = copy.deepcopy(self.e); e["media"]["sha256"] = "0" * 64
        self.assertTrue(self.verify(rec, [e]))
        with open(os.path.join(self.d, "thumb.jpg"), "ab") as f:
            f.write(b"x")                                                    # thumbnail swapped after approval
        self.assertTrue(any("changed" in x for x in self.verify(rec)))

    def test_file_in_release_must_match_the_approved_sha(self):
        bad = {"files": [{"asset": "EP006.mp4", "sha256": "f" * 64}]}
        self.assertTrue(any("sha256" in x for x in self.verify(self.record(), manifest=bad)))

    def test_tampered_record_is_refused(self):
        rec = self.record(); rec["items"][0]["entry_hash"] = "0" * 64
        self.assertTrue(self.verify(rec))
        rec = self.record(); rec["items"][0]["title"] = "Other"
        self.assertTrue(self.verify(rec))


class Consent(Base):
    def test_consent_parser(self):
        ok = ["Одобряю EP006, публикуй завтра в 19:00", "Да, публикуй EP006", "Approve EP006", "Подтверждаю EP006"]
        bad = ["не одобряю EP006", "Одобряю EP005, публикуй", "ок", "давай", "Одобряю EP006?", "Нет, не публикуй EP006", "", "cancel EP006 approve", "stop, approve EP006"]
        for q in ok:
            self.assertTrue(A.consent_ok(q, "EP006"), q)
        for q in bad:
            self.assertFalse(A.consent_ok(q, "EP006"), q)

    def test_bad_quote_in_record_is_refused(self):
        self.assertTrue(any("quote" in x for x in self.verify(self.record(quote="ок"))))


class Rules(Base):
    def test_long_needs_its_own_single_release_approval(self):
        self.assertTrue(any("long" in x for x in self.verify(self.record(scope="short_list"))))
        two = self.record(); two["items"].append(copy.deepcopy(two["items"][0]))
        self.assertTrue(any("long video" in x for x in self.verify(two)))

    def test_short_list_may_hold_only_shorts_and_publish_on_schedule(self):
        shorts = []
        for i in range(3):
            s = copy.deepcopy(self.e); s.update(id=f"EP006-S{i}", kind="short", publish_at=f"2026-10-{26 + i}T01:00:00Z"); shorts.append(s)
        rec = A.make_record(shorts, "EP006 Shorts", "Одобряю EP006 Shorts, список из 3", "short_list", "abc", self.d, now=NOW)
        self.assertEqual(self.verify(rec, shorts), [])
        self.assertTrue(self.verify(self.record(scope="short_list")))          # a long video cannot ride a Shorts list

    def test_time_window_expiry_replay_and_cap(self):
        self.assertTrue(any("30 min" in x for x in self.verify(self.record(), now=NOW + timedelta(hours=30, minutes=45))))   # too close to publish time
        self.assertTrue(any("expired" in x for x in self.verify(self.record(), now=NOW + timedelta(hours=25))))
        rec = self.record()
        self.assertTrue(any("already executed" in x for x in self.verify(rec, ledger=[{"event": "approval_done", "approval_id": rec["approval_id"]}])))
        busy = [{"event": "uploaded", "at": NOW.isoformat(), "sha256": str(i)} for i in range(8)]
        self.assertTrue(any("cap" in x for x in self.verify(rec, ledger=busy)))

    def test_open_issue_and_unfinal_title_block(self):
        e = copy.deepcopy(self.e); e["open_issues"] = ["x"]
        self.assertTrue(any("open issues" in x for x in self.verify(self.record(), [e])))
        e = copy.deepcopy(self.e); e["title_status"] = "pending_owner_choice"
        self.assertTrue(any("not final" in x for x in self.verify(self.record(), [e])))

    def test_undetermined_earlier_upload_blocks(self):
        led = [{"event": "started", "sha256": self.e["media"]["sha256"]}]
        self.assertTrue(any("undetermined" in x for x in self.verify(self.record(), ledger=led)))

    def test_card_shows_local_and_utc_time_and_codes(self):
        c = A.card(self.e, self.d)
        self.assertIn("19:00", c["card_text"]); self.assertIn("12:00 UTC", c["card_text"]); self.assertEqual(len(c["code"]), 9)
        e2 = copy.deepcopy(self.e); e2["publish_at"] = "2026-10-25T13:00:00Z"
        self.assertNotEqual(A.card(e2, self.d)["code"], c["code"])


class Totp(unittest.TestCase):
    SECRET = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"      # RFC 6238 test key "12345678901234567890"

    def test_rfc6238_vector(self):
        self.assertEqual(A.totp(self.SECRET, 59), "287082")

    def test_code_checked_and_single_use(self):
        now = datetime.fromtimestamp(59, timezone.utc)
        step, why = A.totp_check(self.SECRET, "287082", now, []); self.assertIsNone(why)
        self.assertEqual(A.totp_check(self.SECRET, "287082", now, [{"event": "totp_used", "step": step}])[1], "one-time code already used")
        self.assertIsNotNone(A.totp_check(self.SECRET, "000000", now, [])[1])
        self.assertIsNotNone(A.totp_check(self.SECRET, "", now, [])[1])


class ChatRun(Base):
    def args(self, confirm, rec_path):
        return argparse.Namespace(queue=os.path.join(self.d, "queue.json"), mode="chat", ids="all", media_dir=self.d, confirm=confirm, offline=False,
                                  approval=rec_path, manifest=os.path.join(self.d, "media.json"))

    def setup_files(self, rec):
        json.dump({"expected_channel_id": "UC1", "items": [self.e]}, open(os.path.join(self.d, "queue.json"), "w"))
        json.dump(self.manifest, open(os.path.join(self.d, "media.json"), "w")); path = os.path.join(self.d, "rec.json"); json.dump(rec, open(path, "w")); return path

    def run_it(self, rec, confirm=True, now=NOW):
        path = self.setup_files(rec)
        real = {"privacyStatus": "private", "publishAt": self.e["publish_at"], "uploadStatus": "uploaded"}
        with mock.patch.object(P, "DATA_ROOT", self.d), mock.patch.object(A, "datetime") as dt, \
             mock.patch.object(P, "api", return_value={"items": [{"id": "UC1", "snippet": {}}]}), mock.patch.object(P, "inventory", return_value=[]), \
             mock.patch.object(P, "access_token", return_value="t"), mock.patch.object(P, "resumable_upload", return_value={"id": "VID"}) as up, \
             mock.patch.object(P, "set_thumbnail"), mock.patch.object(P, "insert_caption"), mock.patch.object(P, "video_status", return_value=real), \
             mock.patch.object(P, "validate", return_value=[]):
            dt.now.return_value = now; dt.fromisoformat = datetime.fromisoformat; dt.side_effect = None
            with mock.patch.object(P, "datetime") as pdt:
                pdt.now.return_value = now; pdt.fromisoformat = datetime.fromisoformat
                out = P.cmd_queue_run(self.args(confirm, path))
        return out, up

    def test_approved_release_is_uploaded_once_as_private_scheduled_and_marked_done(self):
        rec = self.record()
        out, up = self.run_it(rec)
        self.assertEqual(up.call_count, 1); self.assertEqual(out["items"][0]["status"], "done"); self.assertTrue(out["items"][0]["verified_scheduled"])
        self.assertTrue(any(r.get("event") == "approval_done" for r in P.ledger_read()))
        with self.assertRaises(P.PublishError) as cm:                      # second dispatch of the same approval
            self.run_it(rec)
        self.assertIn("already executed", str(cm.exception))

    def test_dry_run_changes_nothing(self):
        out, up = self.run_it(self.record(), confirm=False)
        up.assert_not_called(); self.assertTrue(out["dry_run"]); self.assertEqual(P.ledger_read(), [])

    def test_stale_approval_is_refused_before_any_network_write(self):
        rec = self.record(); self.e["title"] = "Changed after approval"
        with self.assertRaises(P.PublishError):
            self.run_it(rec)

    def test_totp_required_when_secret_is_set(self):
        os.environ["APPROVAL_TOTP_SECRET"] = Totp.SECRET; os.environ["APPROVAL_TOTP_CODE"] = "000000"
        try:
            with self.assertRaises(P.PublishError) as cm:
                self.run_it(self.record())
            self.assertIn("one-time code", str(cm.exception))
        finally:
            os.environ.pop("APPROVAL_TOTP_SECRET"); os.environ.pop("APPROVAL_TOTP_CODE")


class Workflows(unittest.TestCase):
    ROOT = P.ROOT

    def read(self, n):
        return open(os.path.join(self.ROOT, ".github", "workflows", n)).read()

    def test_legacy_environment_gate_is_still_in_place(self):
        t = self.read("publish.yml")
        self.assertIn("environment:", t); self.assertIn("youtube-approval", t); self.assertIn("UPLOAD $MODE", t)

    def test_chat_workflow_is_gated_serialised_and_injection_safe(self):
        t = self.read("publish-approved.yml")
        self.assertIn("vars.CHAT_PUBLISH_ENABLED == 'true'", t); self.assertIn("group: youtube-publish", t)
        self.assertIn("github.repository_owner", t); self.assertIn("merge-base --is-ancestor", t)
        for line in t.splitlines():
            if line.strip().startswith(("run:", "python3", "git ", "test ")) or (line.startswith("          ") and "${{ inputs." in line and "env" not in line):
                self.assertNotIn("${{ inputs.", line, line)                 # inputs only reach shell through env vars


if __name__ == "__main__":
    unittest.main()
