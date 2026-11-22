import json, os, sys, tempfile, unittest
from datetime import datetime, date, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import engine as E  # noqa: E402

OWNER = "principal:Егор"
T0 = datetime(2026, 11, 19, 8, 0, tzinfo=timezone.utc)          # 15:00 in Asia/Ho_Chi_Minh


def ready_release(state, cfg, now=T0, title="Title A", vid="VIDEO000001", sha="a" * 64):
    r = E.new_release(state, "oa", cfg, day=date(2026, 11, 19), topic={"title": title}, now=now)
    for s in ("scripted", "voiced", "rendered", "qc_passed"):
        E.record_stage(r, s, {"x": s}, now=now)
    v, _ = E.new_version(r, video_sha256=sha, thumbnail_sha256="t" * 64, captions_sha256="c" * 64, title=title,
                         description="d http://x", tags=["a"], duration_s=361.2, files={"video": "v.mp4", "thumbnail": "t.jpg", "captions": "c.srt"}, now=now)
    E.apply_preview_result(r, {"ok": True, "video_sha256": sha, "video_id": vid, "privacyStatus": "private"}, now=now)
    E.save(state, r, now)
    return r


class Base(unittest.TestCase):
    def setUp(self):
        self.state = tempfile.mkdtemp()
        self.cfg = E.load_config()

    def rels(self):
        return E.all_releases(self.state)

    def persist(self, rels):
        for r in rels:
            E.save(self.state, r)


class Rotation(Base):
    def test_owner_rotation(self):
        self.assertEqual(E.production_channel(date(2026, 11, 3), self.cfg), "oa")
        self.assertEqual(E.production_channel(date(2026, 11, 4), self.cfg), "nx")
        self.assertEqual(E.production_channel(date(2026, 11, 17), self.cfg), "oa")
        self.assertEqual(E.production_channel(date(2026, 11, 19), self.cfg), "oa")
        self.assertEqual(E.production_channel(date(2026, 11, 20), self.cfg), "nx")

    def test_both_channels_daily_from_owner_date(self):
        cfg = dict(self.cfg, rotation=dict(self.cfg["rotation"], daily_all_from="2026-11-22"))
        self.assertEqual(E.production_channels(date(2026, 11, 21), cfg), ["oa"])
        self.assertEqual(E.production_channels(date(2026, 11, 22), cfg), ["oa", "nx"])
        self.assertEqual(E.production_channels(date(2026, 12, 1), cfg), ["oa", "nx"])
        no = dict(self.cfg, rotation={k: v for k, v in self.cfg["rotation"].items() if k != "daily_all_from"})
        self.assertEqual(E.production_channels(date(2026, 11, 22), no), ["nx"])

    def test_no_duplicate_release_and_no_repeated_topic(self):
        E.new_release(self.state, "oa", self.cfg, day=date(2026, 11, 19), topic={"title": "Lake Mead from orbit"}, now=T0)
        with self.assertRaises(E.PipelineError):
            E.new_release(self.state, "oa", self.cfg, day=date(2026, 11, 19), topic={"title": "Other"}, now=T0)
        r = self.rels()[0]; r["stage"] = "dropped"; E.save(self.state, r)
        with self.assertRaises(E.PipelineError):
            E.new_release(self.state, "oa", self.cfg, day=date(2026, 11, 21), topic={"title": "Orbit: Lake Mead"}, now=T0)
        r2 = E.new_release(self.state, "oa", self.cfg, day=date(2026, 11, 21), topic={"title": "Aral Sea"}, now=T0)
        self.assertEqual(r2["id"], "oa-20261121-01")


class Slots(Base):
    def test_nearest_free_0800_respects_channel_schedule(self):
        inv = [{"video_id": "x", "privacy": "private", "publishAt": "2026-11-20T01:00:00Z", "seconds": 400}]
        t = E.pick_slot(self.cfg, "oa", "long", inv, [], now=T0)
        self.assertEqual(E.iso(t), "2026-11-21T01:00:00Z")           # 20.11 08:00 is taken -> 21.11 08:00
        t = E.pick_slot(self.cfg, "oa", "long", [], [], now=T0)
        self.assertEqual(E.iso(t), "2026-11-20T01:00:00Z")

    def test_shorts_do_not_block_long_slot_and_open_cards_hold_slots(self):
        inv = [{"video_id": "s", "privacy": "private", "publishAt": "2026-11-20T05:00:00Z", "seconds": 40}]
        self.assertEqual(E.iso(E.pick_slot(self.cfg, "oa", "long", inv, [], now=T0)), "2026-11-20T01:00:00Z")
        r = ready_release(self.state, self.cfg)
        E.make_card(r, self.cfg, E.parse("2026-11-20T01:00:00Z"), now=T0); E.save(self.state, r)
        self.assertEqual(E.iso(E.pick_slot(self.cfg, "oa", "long", [], self.rels(), now=T0)), "2026-11-21T01:00:00Z")


class Cards(Base):
    def card(self, slot="2026-11-20T01:00:00Z"):
        r = ready_release(self.state, self.cfg)
        c = E.make_card(r, self.cfg, E.parse(slot), now=T0)
        E.save(self.state, r)
        return r, c

    def test_ok_button_approves_exactly_that_card(self):
        r, c = self.card()
        rels = self.rels()
        res = E.decide(rels, self.cfg, choice="ok", actor=OWNER, card_id=c["card_id"], now=T0 + timedelta(hours=1))
        self.assertEqual(res["result"], "approved")
        a = res["approval"]
        self.assertEqual((a["video_id"], a["publish_at"], a["version"]), ("VIDEO000001", "2026-11-20T01:00:00Z", 1))
        self.persist(rels)
        req = E.schedule_request(E.load(self.state, r["id"]), self.cfg)
        self.assertEqual(req["publish_at"], "2026-11-20T01:00:00Z")

    def test_repeated_ok_does_nothing_new(self):
        r, c = self.card()
        rels = self.rels()
        first = E.decide(rels, self.cfg, choice="ok", actor=OWNER, card_id=c["card_id"], now=T0 + timedelta(hours=1))
        again = E.decide(rels, self.cfg, choice="ok", actor=OWNER, card_id=c["card_id"], now=T0 + timedelta(hours=2))
        self.assertEqual(again["result"], "duplicate")
        self.assertEqual(again["approval_id"], first["approval"]["approval_id"])
        text = E.decide(rels, self.cfg, choice="ok", actor=OWNER, now=T0 + timedelta(hours=2))
        self.assertEqual(text["result"], "no_open_card")

    def test_expired_card_never_approves(self):
        r, c = self.card()
        rels = self.rels()
        res = E.decide(rels, self.cfg, choice="ok", actor=OWNER, card_id=c["card_id"], now=E.parse("2026-11-20T00:40:00Z"))
        self.assertEqual(res["result"], "expired")
        self.assertIsNone(rels[0]["approval"])

    def test_foreign_actor_is_rejected(self):
        r, c = self.card()
        for actor in ("peer:Someone", "relay:coordinator", "principal:Other"):
            res = E.decide(self.rels(), self.cfg, choice="ok", actor=actor, card_id=c["card_id"], now=T0)
            self.assertEqual(res["result"], "rejected")

    def test_version_replacement_voids_old_card(self):
        r, c = self.card()
        r = E.load(self.state, r["id"])
        E.new_version(r, video_sha256="b" * 64, thumbnail_sha256="t" * 64, captions_sha256="c" * 64, title="Title A",
                      description="d http://x", tags=["a"], duration_s=360, files={}, now=T0)
        E.save(self.state, r)
        res = E.decide(self.rels(), self.cfg, choice="ok", actor=OWNER, card_id=c["card_id"], now=T0 + timedelta(minutes=5))
        self.assertEqual(res["result"], "rejected")
        self.assertIn("void", res["reason"])
        r = E.load(self.state, r["id"])
        self.assertIsNone(r["preview"])                                     # new file -> new private preview first
        with self.assertRaises(E.PipelineError):
            E.make_card(r, self.cfg, E.parse("2026-11-20T01:00:00Z"), now=T0)

    def test_title_or_cover_change_is_a_new_version_too(self):
        r, c = self.card()
        r = E.load(self.state, r["id"])
        v, new = E.new_version(r, video_sha256="a" * 64, thumbnail_sha256="T" * 64, captions_sha256="c" * 64, title="Title A",
                               description="d http://x", tags=["a"], duration_s=361.2, files={}, now=T0)
        self.assertTrue(new)
        self.assertEqual(r["cards"][0]["status"], "void")

    def test_new_card_voids_older_card_of_same_release(self):
        r, c1 = self.card()
        r = E.load(self.state, r["id"])
        c2 = E.make_card(r, self.cfg, E.parse("2026-11-21T01:00:00Z"), now=T0); E.save(self.state, r)
        res = E.decide(self.rels(), self.cfg, choice="ok", actor=OWNER, card_id=c1["card_id"], now=T0)
        self.assertEqual(res["result"], "rejected")
        res = E.decide(self.rels(), self.cfg, choice="ok", actor=OWNER, card_id=c2["card_id"], now=T0)
        self.assertEqual(res["result"], "approved")

    def test_bare_ok_with_two_open_cards_is_ambiguous(self):
        self.card()
        r2 = E.new_release(self.state, "nx", self.cfg, day=date(2026, 11, 20), topic={"title": "Robots"}, now=T0)
        for s in ("scripted", "voiced", "rendered", "qc_passed"):
            E.record_stage(r2, s, {}, now=T0)
        E.new_version(r2, video_sha256="n" * 64, thumbnail_sha256="t" * 64, captions_sha256="c" * 64, title="Robots",
                      description="d", tags=[], duration_s=400, files={}, now=T0)
        E.apply_preview_result(r2, {"ok": True, "video_sha256": "n" * 64, "video_id": "NXVID000001"}, now=T0)
        E.make_card(r2, self.cfg, E.parse("2026-11-21T01:00:00Z"), now=T0); E.save(self.state, r2)
        res = E.decide(self.rels(), self.cfg, choice="ok", actor=OWNER, now=T0)
        self.assertEqual(res["result"], "ambiguous")
        self.assertEqual(len(res["candidates"]), 2)
        self.assertTrue(all(r["approval"] is None for r in self.rels()))

    def test_bare_ok_with_one_open_card_binds_to_it(self):
        r, c = self.card()
        res = E.decide(self.rels(), self.cfg, choice="ok", actor=OWNER, now=T0)
        self.assertEqual((res["result"], res["card_id"]), ("approved", c["card_id"]))

    def test_changes_with_comment(self):
        r, c = self.card()
        rels = self.rels()
        res = E.decide(rels, self.cfg, choice="changes", actor=OWNER, card_id=c["card_id"], comment="короче хук", now=T0)
        self.assertEqual(res["result"], "changes")
        self.assertEqual(rels[0]["stage"], "needs_changes")
        self.assertEqual(E.decide(rels, self.cfg, choice="ok", actor=OWNER, card_id=c["card_id"], now=T0)["result"], "duplicate")
        with self.assertRaises(E.PipelineError):
            E.schedule_request(rels[0], self.cfg)

    def test_ok_words(self):
        for t in ("ок", "ОК", "ok", "Ок!", "да, ок"):
            self.assertTrue(E.is_ok_text(t, self.cfg), t)
        for t in ("не ок", "ок?", "нет", "ok but change the title please and also the cover and the music too"):
            self.assertFalse(E.is_ok_text(t, self.cfg), t)

    def test_card_too_close_to_slot(self):
        r = ready_release(self.state, self.cfg)
        with self.assertRaises(E.PipelineError):
            E.make_card(r, self.cfg, T0 + timedelta(minutes=20), now=T0)


class Restart(Base):
    def test_resume_points_after_a_crash(self):
        r = E.new_release(self.state, "oa", self.cfg, day=date(2026, 11, 19), topic={"title": "X"}, now=T0)
        self.assertEqual(E.resume_point(r), "scripted")
        E.record_stage(r, "scripted", {}, now=T0); E.record_stage(r, "voiced", {"voice_sha256": "v"}, now=T0); E.save(self.state, r)
        r = E.load(self.state, r["id"])                                     # "crash" = reload from disk
        self.assertEqual(E.resume_point(r), "rendered")                    # voice is not generated (paid) again
        notify = E.block(r, "ElevenLabs limit reached", "rendered", now=T0)
        self.assertTrue(notify)
        self.assertFalse(E.block(r, "ElevenLabs limit reached", "rendered", now=T0))   # one notification, not one per retry
        self.assertEqual(E.resume_point(r), "rendered")
        E.unblock(r); self.assertEqual(r["stage"], "voiced")

    def test_scheduled_video_is_never_replaced(self):
        r = ready_release(self.state, self.cfg)
        c = E.make_card(r, self.cfg, E.parse("2026-11-20T01:00:00Z"), now=T0); E.save(self.state, r)
        rels = self.rels(); res = E.decide(rels, self.cfg, choice="ok", actor=OWNER, card_id=c["card_id"], now=T0); self.persist(rels)
        r = E.load(self.state, r["id"])
        E.apply_schedule_result(r, {"ok": True, "approval_id": res["approval"]["approval_id"], "video_id": "VIDEO000001",
                                    "publishAt": "2026-11-20T01:00:00Z", "privacyStatus": "private"}, now=T0)
        self.assertEqual(r["stage"], "scheduled")
        with self.assertRaises(E.PipelineError):
            E.new_version(r, video_sha256="z" * 64, thumbnail_sha256="t", captions_sha256="c", title="T", description="d", tags=[], duration_s=1, files={})
        with self.assertRaises(E.PipelineError):
            E.schedule_request(r, self.cfg)                                 # approval is used up

    def test_slot_taken_result_returns_to_card(self):
        r = ready_release(self.state, self.cfg)
        c = E.make_card(r, self.cfg, E.parse("2026-11-20T01:00:00Z"), now=T0); E.save(self.state, r)
        rels = self.rels(); res = E.decide(rels, self.cfg, choice="ok", actor=OWNER, card_id=c["card_id"], now=T0); self.persist(rels)
        r = E.load(self.state, r["id"])
        E.apply_schedule_result(r, {"ok": False, "approval_id": res["approval"]["approval_id"], "error_kind": "slot_taken"}, now=T0)
        self.assertEqual((r["stage"], r["approval"]["status"]), ("preview_ready", "void"))


if __name__ == "__main__":
    unittest.main()
