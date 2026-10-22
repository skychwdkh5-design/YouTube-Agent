import json, os, sys, tempfile, unittest
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(__file__))
import publish as P

NOW = datetime(2026, 10, 22, tzinfo=timezone.utc)


def spec(d, **kw):
    f = os.path.join(d, "v.mp4"); open(f, "wb").write(b"x" * 10)
    return {"file": f, "kind": "long", "title": "T", "description": "D", "made_for_kids": False,
            "contains_synthetic_media": False, **kw}


class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def test_flags_never_defaulted(self):
        s = spec(self.d); del s["made_for_kids"]
        self.assertRaises(P.PublishError, P.validate, s, NOW)

    def test_schedule_forces_private_and_past_rejected(self):
        b = P.build_body(spec(self.d, privacy="public", publish_at="2026-11-03T15:00:00Z"))
        self.assertEqual(b["status"]["privacyStatus"], "private")
        self.assertEqual(b["status"]["publishAt"], "2026-11-03T15:00:00Z")
        self.assertRaises(P.PublishError, P.validate, spec(self.d, publish_at="2026-01-01T00:00:00Z"), NOW)

    def test_short_gets_hashtag_and_related_link(self):
        b = P.build_body(spec(self.d, kind="short", related_long_url="https://youtu.be/abc"))
        self.assertIn("Full video: https://youtu.be/abc", b["snippet"]["description"])
        self.assertIn("#Shorts", b["snippet"]["description"])
        self.assertEqual(P.build_body(spec(self.d))["status"]["privacyStatus"], "private")

    def test_ledger_blocks_duplicate_even_if_interrupted(self):
        lp = os.path.join(self.d, "l.jsonl")
        self.assertIsNone(P.duplicate_of("h1", lp))
        P.ledger_add({"event": "started", "sha256": "h1"}, lp)
        self.assertIsNotNone(P.duplicate_of("h1", lp))
        self.assertIsNone(P.duplicate_of("h2", lp))

    def test_redact(self):
        os.environ["YT_REFRESH_TOKEN"] = "supersecret"
        self.assertNotIn("supersecret", P.redact("bad supersecret"))


if __name__ == "__main__":
    unittest.main()


# --- queue, ledger states, upload recovery, media manifest -------------------------------------------
import copy
from unittest import mock

QUEUE = json.load(open(os.path.join(P.ROOT, "publish", "queue.json")))["items"]
MEDIA = json.load(open(os.path.join(P.ROOT, "publish", "media.json")))


class Q(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.lp = os.path.join(self.d, "ledger.jsonl")
        P.LEDGER = self.lp

    def entry(self, **kw):
        e = copy.deepcopy(next(x for x in QUEUE if x["kind"] == "short"))
        f = os.path.join(self.d, e["media"]["asset"]); open(f, "wb").write(b"x")
        e["media"]["sha256"] = P.sha256(f)
        e["owner_approval"] = {"approved": True, "sha256": e["media"]["sha256"], "publish_at": e["publish_at"]}
        e["publish_at"] = "2026-10-24T01:00:00Z"; e["owner_approval"]["publish_at"] = e["publish_at"]
        e["related"] = None
        e.update(kw)
        return e

    def test_real_queue_is_consistent_and_blocked_by_default(self):
        self.assertEqual(len(QUEUE), 7)
        sha = {f["asset"]: f["sha256"] for f in MEDIA["files"]}
        for e in QUEUE:
            self.assertEqual(sha[e["media"]["asset"]], e["media"]["sha256"])
            self.assertIs(e["owner_approval"]["approved"], False)       # nothing approved in the repo
            self.assertIs(e["made_for_kids"], False)
            self.assertLessEqual(len(e["title"]), 100)
            self.assertNotRegex(e["title"] + e["description"], "[<>]")
            self.assertTrue(e["publish_at"].endswith("Z"))
        self.assertEqual([e["publish_at"] for e in QUEUE[1:]], [f"2026-10-{d}T01:00:00Z" for d in range(24, 30)])
        self.assertEqual(QUEUE[0]["publish_at"], "2026-10-23T12:00:00Z")   # 19:00 Vietnam
        self.assertEqual(QUEUE[0]["title_status"], "pending_owner_choice")
        pr, spec = P.check_entry(QUEUE[1], "autopilot", self.d, [], NOW, hash_media=False)
        self.assertIsNone(spec); self.assertTrue(any("owner approval" in x for x in pr))

    def test_approved_entry_passes_and_gates_hold(self):
        e = self.entry()
        pr, spec = P.check_entry(e, "autopilot", self.d, [], NOW)
        self.assertEqual(pr, []); self.assertEqual(spec["privacy"], "public")
        self.assertTrue(any("mode" in x for x in P.check_entry(e, "approval", self.d, [], NOW)[0]))
        e2 = self.entry(); e2["owner_approval"]["publish_at"] = "2026-10-30T01:00:00Z"
        self.assertTrue(any("approval" in x for x in P.check_entry(e2, "autopilot", self.d, [], NOW)[0]))
        e3 = self.entry(); open(os.path.join(self.d, e3["media"]["asset"]), "wb").write(b"changed")
        self.assertTrue(any("differs" in x for x in P.check_entry(e3, "autopilot", self.d, [], NOW)[0]))
        e4 = self.entry(title_status="pending_owner_choice")
        self.assertTrue(any("not final" in x for x in P.check_entry(e4, "autopilot", self.d, [], NOW)[0]))

    def test_existing_title_on_channel_blocks(self):
        e = self.entry()
        inv = [{"video_id": "abc", "title": e["title"].upper(), "privacy": "public", "seconds": 20}]
        self.assertTrue(any("already exists" in x for x in P.check_entry(e, "autopilot", self.d, inv, NOW)[0]))

    def test_related_resolution(self):
        e = self.entry(related={"title_contains": "Dubai"})
        L = lambda t, s=600, p="public": {"video_id": "L1", "title": t, "privacy": p, "seconds": s}
        self.assertEqual(P.find_related(e, [L("Dubai Islands from space"), L("Dubai short", 20)])[0], "https://youtu.be/L1")
        self.assertIsNotNone(P.find_related(e, [])[1])
        self.assertIsNotNone(P.find_related(e, [L("Dubai A"), L("Dubai B")])[1])
        self.assertIsNotNone(P.find_related(e, [L("Dubai A", p="private")])[1])

    def test_run_is_idempotent_and_verifies(self):
        e = self.entry(thumbnail=None)
        spec = P.check_entry(e, "autopilot", self.d, [], NOW)[1]
        real = {"privacyStatus": "private", "publishAt": e["publish_at"], "uploadStatus": "uploaded"}
        with mock.patch.object(P, "resumable_upload", return_value={"id": "VID1"}) as up, mock.patch.object(P, "video_status", return_value=real):
            r1 = P.run_entry(e, spec, [], "tok"); r2 = P.run_entry(e, spec, [], "tok")
        self.assertEqual(up.call_count, 1)
        self.assertTrue(r1["verified_scheduled"]); self.assertEqual(r2["steps"], [])
        self.assertEqual(P.ledger_state(e["media"]["sha256"])["state"], "uploaded")

    def test_wrong_real_status_is_flagged(self):
        e = self.entry(thumbnail=None)
        spec = P.check_entry(e, "autopilot", self.d, [], NOW)[1]
        locked = {"privacyStatus": "private", "publishAt": None, "uploadStatus": "uploaded"}
        with mock.patch.object(P, "resumable_upload", return_value={"id": "V"}), mock.patch.object(P, "video_status", return_value=locked):
            self.assertFalse(P.run_entry(e, spec, [], "tok")["verified_scheduled"])

    def test_interrupted_upload_blocks_then_reconciles(self):
        e = self.entry()
        P.ledger_add({"event": "started", "sha256": e["media"]["sha256"], "id": e["id"]}, self.lp)
        with self.assertRaises(P.PublishError):
            P.run_entry(e, {}, [], "tok")
        sha = e["media"]["sha256"]
        P.ledger_add({"event": "abandoned", "sha256": sha}, self.lp)
        self.assertEqual(P.ledger_state(sha)["state"], "none")

    def test_resumable_upload_recovers_from_5xx(self):
        f = os.path.join(self.d, "v.bin"); open(f, "wb").write(b"a" * 100)
        seq = iter([(503, {}, b""), (308, {"Range": "bytes=0-49"}, b""), (200, {}, b'{"id": "OK"}')])
        calls = []
        def fake_http(m, url, headers=None, data=None, timeout=0):
            calls.append((m, (headers or {}).get("Content-Range"))); return next(seq)
        with mock.patch.object(P, "jhttp", return_value=(200, {"Location": "https://up/x"}, {})), \
             mock.patch.object(P, "http", side_effect=fake_http), mock.patch.object(P.time, "sleep"):
            self.assertEqual(P.resumable_upload(f, {}, "t")["id"], "OK")
        self.assertIn("bytes */100", [c[1] for c in calls])        # asked the server for its offset after the 503

    def test_helpers(self):
        self.assertEqual(P.parse_duration("PT6M27S"), 387); self.assertEqual(P.parse_duration("PT1H2M3S"), 3723)
        body, ct = P.multipart({"a": 1}, b"DATA", "text/plain")
        self.assertIn(ct.split("boundary=")[1].encode(), body); self.assertIn(b"DATA", body)

    def test_media_manifest(self):
        import media as M
        self.assertEqual(len(MEDIA["files"]), 7)
        a = {"state": "uploaded", "size": 5, "digest": "sha256:ab"}
        self.assertTrue(M.asset_ok(a, 5, "ab")); self.assertFalse(M.asset_ok(a, 6, "ab")); self.assertFalse(M.asset_ok({**a, "state": "starter"}, 5, "ab"))
        self.assertTrue(all(f["size"] > 0 and len(f["sha256"]) == 64 for f in MEDIA["files"]))


class Thumb(Q):
    def test_long_cover_needs_pass_review_for_exact_file(self):
        e = copy.deepcopy(QUEUE[0]); self.assertEqual(e["thumbnail_review"]["result"], "FAIL")
        pr = P.check_entry(e, "approval", self.d, [], NOW, hash_media=False)[0]
        self.assertTrue(any("thumbnail has no PASS" in x for x in pr))
        e["thumbnail_review"] = {"result": "PASS", "sha256": P.sha256(os.path.join(P.ROOT, e["thumbnail"]))}
        self.assertFalse(any("thumbnail has no PASS" in x for x in P.check_entry(e, "approval", self.d, [], NOW, hash_media=False)[0]))
        e["thumbnail_review"]["sha256"] = "0" * 64
        self.assertTrue(any("thumbnail has no PASS" in x for x in P.check_entry(e, "approval", self.d, [], NOW, hash_media=False)[0]))
