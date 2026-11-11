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
        self.assertIn("Full video: on this channel\nhttps://youtu.be/abc", b["snippet"]["description"])
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

ALL_QUEUE = json.load(open(os.path.join(P.ROOT, "publish", "queue.json")))["items"]
QUEUE = [e for e in ALL_QUEUE if e.get("mode") != "private_test_only"]     # the seven release entries; private-test-only entries are checked in PrivateTest.test_ep006_private_test_entry
PT_ONLY = [e for e in ALL_QUEUE if e.get("mode") == "private_test_only"]
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
        self.assertEqual(QUEUE[0]["title_status"], "final")
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
        self.assertTrue(any("possible duplicate" in x for x in P.check_entry(e, "autopilot", self.d, inv, NOW)[0]))

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
        self.assertEqual(len(MEDIA["files"]), 7 + len(PT_ONLY))
        a = {"state": "uploaded", "size": 5, "digest": "sha256:ab"}
        self.assertTrue(M.asset_ok(a, 5, "ab")); self.assertFalse(M.asset_ok(a, 6, "ab")); self.assertFalse(M.asset_ok({**a, "state": "starter"}, 5, "ab"))
        self.assertTrue(all(f["size"] > 0 and len(f["sha256"]) == 64 for f in MEDIA["files"]))


class Thumb(Q):
    def test_long_cover_needs_pass_review_for_exact_file(self):
        e = copy.deepcopy(QUEUE[0])
        self.assertFalse(any("thumbnail" in x for x in P.check_entry(e, "approval", self.d, [], NOW, hash_media=False)[0]))   # committed review is valid and owner-approved
        e["thumbnail_review"] = {"result": "FAIL", "sha256": e["thumbnail_review"]["sha256"]}
        self.assertTrue(any("thumbnail has no PASS" in x for x in P.check_entry(e, "approval", self.d, [], NOW, hash_media=False)[0]))
        e["thumbnail_review"] = {"result": "PASS", "sha256": P.sha256(os.path.join(P.ROOT, e["thumbnail"]))}
        self.assertTrue(any("not visually approved" in x for x in P.check_entry(e, "approval", self.d, [], NOW, hash_media=False)[0]))
        e["thumbnail_review"]["owner_approved"] = True
        self.assertFalse(any("thumbnail has no PASS" in x for x in P.check_entry(e, "approval", self.d, [], NOW, hash_media=False)[0]))
        e["thumbnail_review"]["sha256"] = "0" * 64
        self.assertTrue(any("thumbnail has no PASS" in x for x in P.check_entry(e, "approval", self.d, [], NOW, hash_media=False)[0]))


FIX = json.load(open(os.path.join(os.path.dirname(__file__), "fixtures", "channel_inventory_2026-10-22.json")))
INV = FIX["videos"]


class RealChannel(unittest.TestCase):
    def test_queue_expects_the_real_channel(self):
        doc = json.load(open(os.path.join(P.ROOT, "publish", "queue.json")))
        self.assertEqual(doc["expected_channel_id"], FIX["channel"]["id"]); self.assertEqual(doc["expected_handle"], "@orbital_atlas")

    def test_every_short_finds_exactly_one_long_video(self):
        want = {"EP002": "XbhVPSCPKwA", "EP003": "RSZwZyRAEAA", "EP004": "D9yQ3X8_J1g"}
        for e in QUEUE:
            if e["kind"] == "short":
                url, why = P.find_related(e, INV)
                self.assertIsNone(why, e["id"]); self.assertEqual(url, "https://youtu.be/" + want[e["id"].split("-")[-1].upper()])

    def test_no_queue_item_conflicts_with_the_channel_today(self):
        for e in QUEUE:
            self.assertEqual(P.find_conflicts(e, INV, "none"), [], e["id"])

    def test_conflict_detection_is_not_title_only(self):
        e = copy.deepcopy(QUEUE[1])
        dup_title = [{"video_id": "x", "title": e["title"] + "!", "seconds": 99, "privacy": "public"}]
        self.assertTrue(P.find_conflicts(e, dup_title, "none"))                    # near-identical title
        same_clip = [{"video_id": "y", "title": "Dubai: no island, only sea (2000 vs 2003)", "seconds": 15.4, "privacy": "public"}]
        self.assertTrue(P.find_conflicts(e, same_clip, "none"))                    # same length + overlapping words
        self.assertEqual(P.find_conflicts(e, same_clip, "uploaded"), [])           # our own upload is fine

    def test_ep005_is_still_blocked_by_owner_gates(self):
        pr = P.check_entry(copy.deepcopy(QUEUE[0]), "approval", tempfile.mkdtemp(), INV, NOW, hash_media=False)[0]
        self.assertTrue(any("owner approval" in x for x in pr)); self.assertFalse(any("thumbnail" in x for x in pr))   # cover approved by the owner
        self.assertTrue(any("media not staged" in x for x in pr)); self.assertFalse(any("open issue" in x for x in pr))


class Decisions(unittest.TestCase):
    def test_ep005_title_is_the_owner_choice_and_final(self):
        e = QUEUE[0]
        self.assertEqual(e["title"], "Saudi Arabia Promised a 170 km City. Here's What Satellites Show.")
        self.assertEqual(e["title_status"], "final"); self.assertTrue(e["description"].startswith(e["title"]))
        meta = json.load(open(os.path.join(P.ROOT, "publish", "assets", "ep005", "metadata.json")))
        self.assertEqual(meta["title"], e["title"])
        self.assertEqual(open(os.path.join(P.ROOT, "publish", "assets", "ep005", "description.txt")).read().strip(), e["description"])

    def test_ep005_scene_ids_match_the_verified_provenance(self):
        ids = json.load(open(os.path.join(P.ROOT, "publish", "assets", "ep005", "metadata.json")))["sentinel2_scenes"]
        self.assertEqual(len(ids), 7)
        for i in ids:
            self.assertIn(i, QUEUE[0]["description"])
        self.assertNotIn("20221009", QUEUE[0]["description"]); self.assertNotIn("20261018", QUEUE[0]["description"])

    def test_ai_decision_for_ep002_short02_stays_open(self):
        e = next(x for x in QUEUE if x["id"] == "short-02-ep002")
        self.assertIsNone(e["contains_synthetic_media"]); self.assertEqual(e["ai_disclosure_status"], "PENDING_OWNER_REVIEW")
        e2 = copy.deepcopy(e); e2["owner_approval"] = {"approved": True, "sha256": e2["media"]["sha256"], "publish_at": e2["publish_at"]}
        pr = P.check_entry(e2, "autopilot", tempfile.mkdtemp(), INV, NOW, hash_media=False)[0]
        self.assertTrue(any("open issue" in x for x in pr))

    def test_shorts_link_to_verified_long_videos_with_real_titles(self):
        for e in QUEUE[1:]:
            url, title, why = P.resolve_related(e, INV)
            self.assertIsNone(why, e["id"]); self.assertNotIn("Dubai Islands'", e["description"]); self.assertNotIn("Satellites Reveal Why", e["description"])
            b = P.build_body({"kind": "short", "title": "t", "description": e["description"], "made_for_kids": False, "contains_synthetic_media": False,
                              "related_long_url": url, "related_long_title": title})
            self.assertIn(title, b["snippet"]["description"]); self.assertEqual(b["snippet"]["description"].count(url), 1)

    def test_wrong_related_id_or_title_is_refused(self):
        e = copy.deepcopy(QUEUE[1]); e["related"]["title"] = "Some other title"
        self.assertIsNotNone(P.resolve_related(e, INV)[2])
        e["related"] = {"video_id": "Si5BEK3aQDw"}                      # a Short, not a long video
        self.assertIsNotNone(P.resolve_related(e, INV)[2])


class CoverApproval(unittest.TestCase):
    def test_owner_approval_is_bound_to_the_exact_file(self):
        e = copy.deepcopy(QUEUE[0]); rv = e["thumbnail_review"]
        self.assertIs(rv["owner_approved"], True)
        self.assertEqual(rv["sha256"], P.sha256(os.path.join(P.ROOT, e["thumbnail"])))
        e["thumbnail_review"]["sha256"] = "0" * 64                      # file changed after approval -> blocked again
        self.assertTrue(any("thumbnail has no PASS" in x for x in P.check_entry(e, "approval", tempfile.mkdtemp(), [], NOW, hash_media=False)[0]))


class PrivateTest(Q):
    def pt_entry(self):
        e = copy.deepcopy(next(x for x in QUEUE if x["id"] == "short-01-ep002"))
        f = os.path.join(self.d, e["media"]["asset"])
        with open(f, "wb") as fh:
            fh.write(b"x")
        e["media"]["sha256"] = P.sha256(f); e["related"] = None
        return e

    def test_only_short_01_is_cleared_and_owner_approval_is_untouched(self):
        self.assertEqual([x["id"] for x in ALL_QUEUE if x.get("private_test_allowed")], ["short-01-ep002", "ep006-cut-preview"])
        for x in QUEUE:
            if x["id"] != "short-01-ep002":
                pr = P.check_entry(copy.deepcopy(x), "private_test", self.d, [], NOW, hash_media=False)[0]
                self.assertTrue(any("not cleared" in y for y in pr), x["id"])
        e = self.pt_entry(); before = copy.deepcopy(e["owner_approval"])
        pr, spec = P.check_entry(e, "private_test", self.d, [], NOW)
        self.assertEqual(pr, []); self.assertEqual(e["owner_approval"], before); self.assertIs(before["approved"], False)

    def test_ep006_private_test_entry(self):
        e = copy.deepcopy(next(x for x in ALL_QUEUE if x["id"] == "ep006-cut-preview"))
        self.assertEqual(e["mode"], "private_test_only"); self.assertIs(e["owner_approval"]["approved"], False); self.assertNotEqual(e["title_status"], "final")
        self.assertEqual(e["media"]["sha256"], next(f["sha256"] for f in MEDIA["files"] if f["asset"] == e["media"]["asset"]))
        for mode in ("approval", "autopilot"):                          # never picked up by a normal run
            self.assertEqual(P.check_entry(copy.deepcopy(e), mode, self.d, [], NOW, hash_media=False)[1], None)
        f = os.path.join(self.d, e["media"]["asset"])
        with open(f, "wb") as fh:
            fh.write(b"x")
        e["media"]["sha256"] = P.sha256(f)
        pr, spec = P.check_entry(e, "private_test", self.d, [], NOW)
        self.assertEqual(pr, []); self.assertEqual(spec["privacy"], "private"); self.assertNotIn("publish_at", spec); self.assertTrue(spec["title"].startswith("[PRIVATE TEST] "))
        body = P.build_body(spec)
        self.assertEqual(body["status"]["privacyStatus"], "private"); self.assertNotIn("publishAt", body["status"])

    def test_spec_is_private_unscheduled_and_marked_test(self):
        pr, spec = P.check_entry(self.pt_entry(), "private_test", self.d, [], NOW)
        body = P.build_body(spec)
        self.assertEqual(body["status"]["privacyStatus"], "private"); self.assertNotIn("publishAt", body["status"])
        self.assertTrue(body["snippet"]["title"].startswith("[PRIVATE TEST] ")); self.assertIs(body["status"]["selfDeclaredMadeForKids"], False)

    def test_run_uploads_once_verifies_and_logs(self):
        e = self.pt_entry(); spec = P.check_entry(e, "private_test", self.d, [], NOW)[1]
        real = {"privacyStatus": "private", "publishAt": None, "uploadStatus": "uploaded", "processing": "processing", "madeForKids": False, "title": spec["title"]}
        with mock.patch.object(P, "resumable_upload", return_value={"id": "TESTVID"}) as up, mock.patch.object(P, "video_status", return_value=real):
            r1 = P.run_private_test(e, spec, [], "tok"); r2 = P.run_private_test(e, spec, [], "tok")
        self.assertEqual(up.call_count, 1); self.assertTrue(r1["verified_private"]); self.assertEqual(r1["private_url"], "https://youtu.be/TESTVID")
        ev = [r for r in P.ledger_read() if r.get("event") == "verified"][0]
        for k in ("video_id", "file_sha256", "uploadStatus", "processingStatus", "privacyStatus", "notes"):
            self.assertIn(k, ev)
        self.assertEqual(ev["file_sha256"], e["media"]["sha256"]); self.assertEqual(P.ledger_state(e["media"]["sha256"])["state"], "none")   # real upload is not blocked

    def test_undetermined_attempt_never_reuploads(self):
        e = self.pt_entry(); spec = P.check_entry(e, "private_test", self.d, [], NOW)[1]
        P.ledger_add({"event": "started", "sha256": "private_test:" + e["media"]["sha256"], "file_sha256": e["media"]["sha256"], "kind": "private_test"}, self.lp)
        real = {"privacyStatus": "private", "publishAt": None, "uploadStatus": "processed", "processing": "succeeded"}
        with mock.patch.object(P, "resumable_upload") as up, mock.patch.object(P, "video_status", return_value=real):
            with self.assertRaises(P.PublishError):
                P.run_private_test(e, spec, [], "tok")                                            # not on the channel: stop, do not upload
            r = P.run_private_test(e, spec, [{"video_id": "FOUND", "title": spec["title"], "privacy": "private", "seconds": 15}], "tok")
        up.assert_not_called(); self.assertEqual(r["video_id"], "FOUND")                          # found it first, adopted it

    def test_visible_result_is_flagged(self):
        e = self.pt_entry(); spec = P.check_entry(e, "private_test", self.d, [], NOW)[1]
        with mock.patch.object(P, "resumable_upload", return_value={"id": "V"}), mock.patch.object(P, "video_status", return_value={"privacyStatus": "public", "uploadStatus": "uploaded"}):
            self.assertFalse(P.run_private_test(e, spec, [], "tok")["verified_private"])

    def test_needs_exactly_one_id_and_live_inventory(self):
        import argparse
        for ids in ("all", "short-01-ep002,short-02-ep002"):
            with self.assertRaises(P.PublishError):
                P.cmd_queue_run(argparse.Namespace(queue=P.QUEUE, mode="private_test", ids=ids, media_dir=self.d, confirm=False, offline=True))

    def test_recorded_test_video_does_not_block_the_real_upload_later(self):
        real_entry = copy.deepcopy(QUEUE[1])
        twin = [{"video_id": "TESTVID", "title": "[PRIVATE TEST] " + real_entry["title"], "seconds": 15.0, "privacy": "private"}]
        self.assertTrue(P.find_conflicts(real_entry, twin, "none"))
        P.ledger_add({"event": "uploaded", "kind": "private_test", "video_id": "TESTVID", "sha256": "private_test:abc"}, self.lp)
        self.assertEqual(P.find_conflicts(real_entry, twin, "none", P.test_video_ids()), [])
