import json, os, sys, tempfile, unittest
from datetime import datetime, timezone
from unittest import mock
sys.path.insert(0, os.path.dirname(__file__))
import publish as P
import takoe_schedule as T

UTC = timezone.utc
T.READBACK_WAIT = 0


def ict(s):
    return T.local(s)


class Slots(unittest.TestCase):
    def test_first_slot_at_least_30_min_on_even_ict_hour(self):
        now = datetime(2026, 11, 27, 10, 45, tzinfo=UTC)          # 17:45 ICT -> 18:00 is only 15 min away
        self.assertEqual([ict(x) for x in T.plan_slots(3, now, [])], ["2026-11-27 20:00", "2026-11-27 22:00", "2026-11-28 00:00"])
        now = datetime(2026, 11, 27, 10, 30, tzinfo=UTC)          # exactly 30 min before 18:00 ICT
        self.assertEqual(ict(T.plan_slots(1, now, [])[0]), "2026-11-27 18:00")

    def test_block_continues_after_existing_when_gap_too_small(self):
        now = datetime(2026, 11, 27, 10, 45, tzinfo=UTC)
        taken = [datetime(2026, 11, 27, 15, 0, tzinfo=UTC)]       # 22:00 ICT already scheduled
        self.assertEqual([ict(x) for x in T.plan_slots(2, now, taken)], ["2026-11-28 00:00", "2026-11-28 02:00"])
        self.assertEqual([ict(x) for x in T.plan_slots(1, now, taken)], ["2026-11-27 20:00"])

    def test_after_keeps_series_order(self):
        now = datetime(2026, 11, 27, 10, 45, tzinfo=UTC)
        after = datetime(2026, 11, 27, 19, 0, tzinfo=UTC)          # 02:00 ICT, our last scheduled episode
        self.assertEqual(ict(T.plan_slots(1, now, [after], after=after)[0]), "2026-11-28 04:00")


def queue(tmp):
    path = os.path.join(tmp, "a.mp4")
    open(path, "wb").write(b"x")
    e = {"id": "A1", "series": "S", "episode": 1, "version": "v1", "kind": "short",
         "media": {"asset": "a.mp4", "sha256": P.sha256(path)}, "title": "T1", "description": "d",
         "made_for_kids": False, "contains_synthetic_media": True, "default_language": "ru", "private_test_allowed": True}
    q = os.path.join(tmp, "q.json")
    json.dump({"expected_channel_id": T.EXPECTED_CHANNEL_ID, "min_lead_minutes": 30, "items": [e]}, open(q, "w"))
    return q, e


class Behaviour(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.q, self.e = queue(self.tmp)
        self.j = os.path.join(self.tmp, "journal.jsonl")
        self.args = ["--queue", self.q, "--media-dir", self.tmp, "--journal", self.j]

    def test_channel_mismatch_sends_nothing(self):
        other = {"items": [{"id": "UC_other", "snippet": {"title": "Orbital Atlas"}}]}
        with mock.patch.object(P, "access_token", return_value="t"), mock.patch.object(P, "api", return_value=other) as api, \
             mock.patch.object(P, "resumable_upload") as up:
            rc = T.main(["schedule", *self.args, "--confirm"])
        self.assertEqual(rc, 1)
        up.assert_not_called()
        self.assertEqual(api.call_count, 1)

    def run_schedule(self, inv, real):
        good = {"items": [{"id": T.EXPECTED_CHANNEL_ID, "snippet": {"title": "Такое бывает"}}]}
        with mock.patch.object(P, "access_token", return_value="t"), mock.patch.object(P, "api", return_value=good), \
             mock.patch.object(P, "inventory", return_value=inv), mock.patch.object(P, "validate", return_value=[]), \
             mock.patch.object(P, "resumable_upload", return_value={"id": "VID1"}) as up, \
             mock.patch.object(T, "set_schedule") as ss, mock.patch.object(T, "full_status", side_effect=real):
            out = T.cmd_schedule(T_args(self.q, self.tmp, self.j))
        return out, up, ss

    def test_upload_then_confirm_then_no_duplicate(self):
        def real(vid, tok):
            row = [r for r in T.jread(self.j) if r.get("event") == "started"][-1]
            return {"found": True, "privacyStatus": "private", "publishAt": row["publish_at"], "uploadStatus": "uploaded"}
        out, up, ss = self.run_schedule([], real)
        self.assertTrue(out["items"][0]["confirmed"])
        up.assert_called_once()
        inv = [{"video_id": "VID1", "title": "T1", "privacy": "private", "publishAt": out["items"][0]["publish_at"], "seconds": 1}]
        out2, up2, ss2 = self.run_schedule(inv, lambda v, t: {"found": True, "privacyStatus": "private", "publishAt": out["items"][0]["publish_at"], "uploadStatus": "processed"})
        up2.assert_not_called(); ss2.assert_not_called()
        self.assertEqual(out2["items"][0]["action"], "keep")

    def test_private_test_video_is_scheduled_not_reuploaded(self):
        T.jadd(self.j, {"event": "uploaded", "id": "A1", "sha256": self.e["media"]["sha256"], "video_id": "VT", "private_test": True})
        inv = [{"video_id": "VT", "title": "T1", "privacy": "private", "publishAt": None, "seconds": 1}]
        def real(vid, tok):
            pa = ss.call_args[0][2]
            return {"found": True, "privacyStatus": "private", "publishAt": pa, "uploadStatus": "processed"}
        ss = mock.MagicMock()
        good = {"items": [{"id": T.EXPECTED_CHANNEL_ID, "snippet": {"title": "Такое бывает"}}]}
        with mock.patch.object(P, "access_token", return_value="t"), mock.patch.object(P, "api", return_value=good), \
             mock.patch.object(P, "inventory", return_value=inv), mock.patch.object(P, "validate", return_value=[]), \
             mock.patch.object(P, "resumable_upload") as up, mock.patch.object(T, "set_schedule", ss), \
             mock.patch.object(T, "full_status", side_effect=real):
            out = T.cmd_schedule(T_args(self.q, self.tmp, self.j))
        up.assert_not_called()
        self.assertEqual(out["items"][0]["action"], "set_publishAt_on_existing_video")
        self.assertTrue(out["items"][0]["confirmed"])

    def test_unconfirmed_schedule_stops_batch(self):
        out, up, ss = self.run_schedule([], lambda v, t: {"found": True, "privacyStatus": "private", "publishAt": None, "uploadStatus": "uploaded"})
        self.assertFalse(out["items"][0]["confirmed"])
        self.assertTrue(out["stopped"])

    def test_untracked_private_video_with_same_title_is_skipped(self):
        inv = [{"video_id": "VX", "title": "T1", "privacy": "private", "publishAt": None, "seconds": 1}]
        out, up, ss = self.run_schedule(inv, lambda v, t: {})
        up.assert_not_called()
        self.assertEqual(out["items"][0]["action"], "skip")


class Fixed(unittest.TestCase):
    def test_owner_time_moves_existing_scheduled_video(self):
        tmp = tempfile.mkdtemp(); q, e = queue(tmp); j = os.path.join(tmp, "j.jsonl")
        doc = json.load(open(q)); doc["items"][0]["publish_at"] = "2026-11-29T12:00:00+07:00"; json.dump(doc, open(q, "w"))
        T.jadd(j, {"event": "uploaded", "id": "A1", "sha256": e["media"]["sha256"], "video_id": "V1"})
        T.jadd(j, {"event": "scheduled", "id": "A1", "sha256": e["media"]["sha256"], "video_id": "V1", "publish_at": "2026-11-28T03:00:00Z", "confirmed": True})
        inv = [{"video_id": "V1", "title": "T1", "privacy": "private", "publishAt": "2026-11-28T03:00:00Z", "seconds": 1}]
        now = datetime(2026, 11, 27, 18, 0, tzinfo=UTC)
        with mock.patch.object(P, "validate", return_value=[]):
            rows = T.build_plan(T.load(q), tmp, j, inv, now)
        self.assertEqual(rows[0]["action"], "set_schedule")
        self.assertEqual(rows[0]["publish_at"], "2026-11-29T05:00:00Z")
        T.jadd(j, {"event": "scheduled", "id": "A1", "sha256": e["media"]["sha256"], "video_id": "V1", "publish_at": "2026-11-29T05:00:00Z", "confirmed": True})
        with mock.patch.object(P, "validate", return_value=[]):
            rows = T.build_plan(T.load(q), tmp, j, inv, now)
        self.assertEqual(rows[0]["action"], "keep")


class Replace(unittest.TestCase):
    def test_new_file_version_uploads_with_old_time_and_unschedules_old(self):
        tmp = tempfile.mkdtemp(); q, e = queue(tmp); j = os.path.join(tmp, "j.jsonl")
        T.jadd(j, {"event": "uploaded", "id": "A1", "sha256": "oldsha", "video_id": "OLD"})
        T.jadd(j, {"event": "scheduled", "id": "A1", "sha256": "oldsha", "video_id": "OLD", "publish_at": "2099-01-01T05:00:00Z", "confirmed": True})
        inv = [{"video_id": "OLD", "title": "T1", "privacy": "private", "publishAt": "2099-01-01T05:00:00Z", "seconds": 1}]
        status = {"OLD": {"found": True, "privacyStatus": "private", "publishAt": None, "uploadStatus": "processed"},
                  "NEW": {"found": True, "privacyStatus": "private", "publishAt": "2099-01-01T05:00:00Z", "uploadStatus": "uploaded"}}
        good = {"items": [{"id": T.EXPECTED_CHANNEL_ID, "snippet": {"title": "Такое бывает"}}]}
        with mock.patch.object(P, "access_token", return_value="t"), mock.patch.object(P, "api", return_value=good) as api, \
             mock.patch.object(P, "inventory", return_value=inv), mock.patch.object(P, "validate", return_value=[]), \
             mock.patch.object(P, "resumable_upload", return_value={"id": "NEW"}) as up, \
             mock.patch.object(T, "full_status", side_effect=lambda v, t: status[v]):
            out = T.cmd_schedule(T_args(q, tmp, j))
        up.assert_called_once()
        self.assertEqual(up.call_args[0][1]["status"]["publishAt"], "2099-01-01T05:00:00Z")
        item = out["items"][0]
        self.assertTrue(item["confirmed"])
        self.assertEqual(item["replaced"][0], {"video_id": "OLD", "unscheduled": True, "privacyStatus": "private", "publishAt": None})
        puts = [c for c in api.call_args_list if c[0][0] == "PUT"]
        self.assertEqual(puts[0][1]["body"]["id"], "OLD")
        self.assertNotIn("publishAt", puts[0][1]["body"]["status"])
        self.assertFalse(any(c[0][0] == "DELETE" for c in api.call_args_list))


class Refused(unittest.TestCase):
    def test_refused_upload_session_is_not_a_pending_upload(self):
        tmp = tempfile.mkdtemp(); j = os.path.join(tmp, "j.jsonl")
        T.jadd(j, {"event": "started", "id": "A1", "sha256": "s"})
        T.jadd(j, {"event": "error", "id": "A1", "sha256": "s", "message": "upload session refused (400): uploadLimitExceeded"})
        self.assertEqual(T.jstate(j, "A1", "s")["state"], "none")
        T.jadd(j, {"event": "started", "id": "A1", "sha256": "s"})
        T.jadd(j, {"event": "error", "id": "A1", "sha256": "s", "message": "upload kept failing"})
        self.assertEqual(T.jstate(j, "A1", "s")["state"], "started")


def T_args(q, d, j):
    import argparse
    return argparse.Namespace(queue=q, media_dir=d, journal=j, confirm=True, ids=None, offline=False)


if __name__ == "__main__":
    unittest.main()
