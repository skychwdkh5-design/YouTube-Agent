"""yt_ops against a fake YouTube: no network. Covers re-runs, lost responses, repeated approvals, timeouts and slot conflicts."""
import argparse, json, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import yt_ops as O  # noqa: E402
P = O.P

CH = "UC2QxQJhUe9Q5NMRNb6M9ddw"


class FakeYT:
    def __init__(self):
        self.videos, self.uploads, self.updates, self.fail_update_once = {}, 0, 0, None

    def token(self):
        return "tok"

    def upload(self, path, body, token):
        self.uploads += 1
        vid = f"VID{self.uploads:08d}"
        self.videos[vid] = {"title": body["snippet"]["title"], "tags": body["snippet"]["tags"], "privacyStatus": body["status"]["privacyStatus"],
                            "publishAt": body["status"].get("publishAt"), "seconds": 400}
        return {"id": vid}

    def api(self, method, path, params=None, body=None, token=None):
        if path == "channels":
            return {"items": [{"id": CH}]}
        if path == "videos" and method == "GET":
            v = self.videos.get(params["id"])
            return {"items": [{"snippet": {"tags": v["tags"]}}] if v else []}
        if path == "videos" and method == "PUT":
            if self.fail_update_once:
                kind = self.fail_update_once; self.fail_update_once = None
                if kind == "applied_then_timeout":
                    self.updates += 1; self.videos[body["id"]].update(publishAt=body["status"]["publishAt"])
                raise OSError("timed out")
            self.updates += 1
            self.videos[body["id"]].update(privacyStatus=body["status"]["privacyStatus"], publishAt=body["status"]["publishAt"])
            return {}
        raise AssertionError(path)

    def status(self, vid, token=None):
        v = self.videos.get(vid)
        if not v:
            return {"video_id": vid, "found": False}
        return {"video_id": vid, "found": True, "title": v["title"], "privacyStatus": v["privacyStatus"], "publishAt": v["publishAt"],
                "uploadStatus": "processed", "processing": "succeeded"}

    def inventory(self, token=None):
        return [{"video_id": k, "title": v["title"], "privacy": v["privacyStatus"], "publishAt": v["publishAt"], "seconds": v["seconds"],
                 "publishedAt": None} for k, v in self.videos.items()]


class Ops(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.ledger = os.path.join(self.d, "ledger.jsonl")
        self.yt = FakeYT()
        for n, data in (("v.mp4", b"video-bytes"), ("t.jpg", b"\xff\xd8\xffcover"), ("c.srt", b"1\n00:00:00,000 --> 00:00:01,000\nHi\n")):
            open(os.path.join(self.d, n), "wb").write(data)
        self.sha = P.sha256(os.path.join(self.d, "v.mp4"))
        self.patches = [mock.patch.object(P, "LEDGER", self.ledger), mock.patch.object(P, "access_token", self.yt.token),
                        mock.patch.object(P, "resumable_upload", self.yt.upload), mock.patch.object(P, "api", self.yt.api),
                        mock.patch.object(P, "video_status", self.yt.status), mock.patch.object(P, "inventory", self.yt.inventory),
                        mock.patch.object(P, "set_thumbnail", lambda *a: {}), mock.patch.object(P, "insert_caption", lambda *a: {}),
                        mock.patch.object(P, "validate", lambda spec, now=None: []), mock.patch.object(O.time, "sleep", lambda s: None)]
        for p in self.patches:
            p.start()
        self.addCleanup(lambda: [p.stop() for p in self.patches])

    def preview_req(self):
        req = {"op": "preview", "release": "oa-20261119-01", "channel": "oa", "channel_id": CH, "version": 1, "version_hash": "h1",
               "video_sha256": self.sha, "title": "T", "description": "D", "tags": ["x"], "files": {"video": "v.mp4", "thumbnail": "t.jpg", "captions": "c.srt"},
               "thumbnail_sha256": P.sha256(os.path.join(self.d, "t.jpg")), "captions_sha256": P.sha256(os.path.join(self.d, "c.srt")),
               "made_for_kids": False, "contains_synthetic_media": False, "marker_tag": "pipeline-oa-20261119-01-v1"}
        p = os.path.join(self.d, "preq.json"); json.dump(req, open(p, "w")); return p

    def args(self, req, confirm=True):
        return argparse.Namespace(request=req, media_dir=self.d, confirm=confirm, out=None)

    def test_preview_twice_uploads_once(self):
        r1 = O.op_preview(self.args(self.preview_req()))
        r2 = O.op_preview(self.args(self.preview_req()))
        self.assertTrue(r1["ok"]); self.assertEqual(r1["video_id"], r2["video_id"]); self.assertEqual(self.yt.uploads, 1)
        self.assertEqual(self.yt.videos[r1["video_id"]]["privacyStatus"], "private")
        self.assertIsNone(self.yt.videos[r1["video_id"]]["publishAt"])

    def test_dry_run_sends_nothing(self):
        r = O.op_preview(self.args(self.preview_req(), confirm=False))
        self.assertTrue(r["dry_run"]); self.assertEqual(self.yt.uploads, 0)

    def test_lost_upload_response_is_adopted_not_reuploaded(self):
        req = self.preview_req()
        real_upload = self.yt.upload
        def crash(path, body, token):
            real_upload(path, body, token); raise OSError("connection reset")
        with mock.patch.object(P, "resumable_upload", crash):
            with self.assertRaises(OSError):
                O.op_preview(self.args(req))
        r = O.op_preview(self.args(req))
        self.assertTrue(r["ok"]); self.assertEqual(self.yt.uploads, 1)

    def test_undetermined_recent_start_refuses(self):
        P.ledger_add({"event": "pipeline_started", "key": "preview:" + self.sha, "release": "oa-20261119-01"})
        with self.assertRaises(O.OpsError) as cm:
            O.op_preview(self.args(self.preview_req()))
        self.assertEqual(cm.exception.kind, "undetermined"); self.assertEqual(self.yt.uploads, 0)

    def test_tampered_file_refused(self):
        req = self.preview_req(); open(os.path.join(self.d, "v.mp4"), "wb").write(b"other")
        with self.assertRaises(O.OpsError):
            O.op_preview(self.args(req))

    def schedule_req(self, vid, at=None, approval_id="a" * 32):
        at = at or (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%dT01:00:00Z")
        appr = {"approval_id": approval_id, "release": "oa-20261119-01", "card_id": "card-1", "version_hash": "h1", "video_sha256": self.sha,
                "video_id": vid, "publish_at": at, "actor": "principal:Егор", "status": "valid"}
        req = {"op": "schedule", "release": "oa-20261119-01", "channel_id": CH, "approval": appr, "video_id": vid, "publish_at": at,
               "version_hash": "h1", "video_sha256": self.sha, "made_for_kids": False, "contains_synthetic_media": False}
        p = os.path.join(self.d, f"sreq-{approval_id[:4]}.json"); json.dump(req, open(p, "w")); return p, at

    def test_schedule_once_even_if_repeated(self):
        vid = O.op_preview(self.args(self.preview_req()))["video_id"]
        req, at = self.schedule_req(vid)
        r1 = O.op_schedule(self.args(req)); r2 = O.op_schedule(self.args(req))
        self.assertTrue(r1["ok"] and r2["ok"]); self.assertEqual(self.yt.updates, 1)
        self.assertEqual(self.yt.videos[vid]["publishAt"], at)

    def test_timeout_after_applied_update_is_read_back(self):
        vid = O.op_preview(self.args(self.preview_req()))["video_id"]
        req, at = self.schedule_req(vid)
        self.yt.fail_update_once = "applied_then_timeout"
        r = O.op_schedule(self.args(req))
        self.assertTrue(r["ok"]); self.assertEqual(self.yt.updates, 1)

    def test_second_approval_cannot_move_a_scheduled_video(self):
        vid = O.op_preview(self.args(self.preview_req()))["video_id"]
        req, _ = self.schedule_req(vid); O.op_schedule(self.args(req))
        req2, _ = self.schedule_req(vid, at=(datetime.now(timezone.utc) + timedelta(days=3)).strftime("%Y-%m-%dT01:00:00Z"), approval_id="b" * 32)
        with self.assertRaises(O.OpsError):
            O.op_schedule(self.args(req2))
        self.assertEqual(self.yt.updates, 1)

    def test_foreign_video_or_actor_refused(self):
        vid = O.op_preview(self.args(self.preview_req()))["video_id"]
        self.yt.videos["OTHER000001"] = {"title": "x", "tags": [], "privacyStatus": "private", "publishAt": None, "seconds": 400}
        req, _ = self.schedule_req("OTHER000001")
        with self.assertRaises(O.OpsError):
            O.op_schedule(self.args(req))
        req, _ = self.schedule_req(vid)
        d = json.load(open(req)); d["approval"]["actor"] = "relay:coordinator"; json.dump(d, open(req, "w"))
        with self.assertRaises(O.OpsError):
            O.op_schedule(self.args(req))
        self.assertEqual(self.yt.updates, 0)

    def test_expired_slot_refused(self):
        vid = O.op_preview(self.args(self.preview_req()))["video_id"]
        req, _ = self.schedule_req(vid, at=(datetime.now(timezone.utc) + timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ"))
        with self.assertRaises(O.OpsError) as cm:
            O.op_schedule(self.args(req))
        self.assertEqual(cm.exception.kind, "expired")

    def test_slot_taken_on_channel(self):
        vid = O.op_preview(self.args(self.preview_req()))["video_id"]
        req, at = self.schedule_req(vid)
        self.yt.videos["MANUAL00001"] = {"title": "manual", "tags": [], "privacyStatus": "private", "publishAt": at, "seconds": 500}
        with self.assertRaises(O.OpsError) as cm:
            O.op_schedule(self.args(req))
        self.assertEqual(cm.exception.kind, "slot_taken"); self.assertEqual(self.yt.updates, 0)


if __name__ == "__main__":
    unittest.main()
