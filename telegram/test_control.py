import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(__file__))
import control  # noqa: E402
import tg  # noqa: E402

CHAT = "987654321"
ENV = {"TELEGRAM_CHAT_ID": CHAT, "TELEGRAM_CALLBACK_SECRET": "s" * 40, "GITHUB_ACTIONS": "",
       "TELEGRAM_BOT_TOKEN": "123456789:AAFakeFakeFakeFakeFakeFakeFakeFake12"}


def approval(**kw):
    n = {"kind": "APPROVAL_REQUIRED", "project": "OrbitalAtlas", "need": "Одобрить EP016 к публикации",
         "why_blocked": "Публикация длинного ролика требует твоего согласия",
         "on_approve": "Claude запишет решение; публикация - только по правилам чата",
         "on_reject": "Ролик не публикуется", "dedup_key": "OrbitalAtlas/EP016/publish",
         "link": "https://github.com/skychwdkh5-design/YouTube-Agent/issues/1", "button_safe": True}
    n.update(kw)
    return n


class Sender:
    def __init__(self, fail=0):
        self.sent, self.fail = [], fail

    def __call__(self, text, buttons, reply_to):
        if self.fail > 0:
            self.fail -= 1
            raise tg.TgError("sendMessage failed: 502 Bad Gateway")
        self.sent.append({"text": text, "buttons": buttons, "reply_to": reply_to})
        return {"message_id": 100 + len(self.sent)}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.env = mock.patch.dict(os.environ, ENV)
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()


class Suppression(Base):
    def test_routine_events_are_never_sent(self):
        s = Sender()
        for kind in ["video_ready", "error", "info", "progress", "started", "render_done", "published",
                     "daily_report", "success", "", "approval_required"]:
            r = control.request(self.root, {**approval(), "kind": kind}, 1000, sender=s)
            self.assertFalse(r["sent"]); self.assertTrue(r["suppressed"], kind)
        self.assertEqual(s.sent, [])

    def test_auto_resolvable_is_suppressed(self):
        s = Sender()
        r = control.request(self.root, approval(auto_resolvable=True), 1000, sender=s)
        self.assertTrue(r["suppressed"]); self.assertEqual(s.sent, [])

    def test_mandatory_fields_and_recovery(self):
        s = Sender()
        for drop in control.REQUIRED:
            n = approval(); n.pop(drop)
            self.assertFalse(control.request(self.root, n, 1000, sender=s)["sent"], drop)
        blk = approval(kind="HUMAN_INTERVENTION_REQUIRED", dedup_key="x")
        self.assertIn("recovery", control.request(self.root, blk, 1000, sender=s)["reason"])
        self.assertFalse(control.request(self.root, approval(project="Other"), 1000, sender=s)["sent"])
        self.assertFalse(control.request(self.root, approval(link="http://x"), 1000, sender=s)["sent"])
        self.assertEqual(s.sent, [])


class Content(Base):
    def test_message_has_every_required_part(self):
        s = Sender()
        self.assertTrue(control.request(self.root, approval(), 1000, sender=s)["sent"])
        t = s.sent[0]["text"]
        for part in ["Нужно твоё одобрение", "Проект: Orbital Atlas", "Что нужно от тебя", "Почему Claude не может",
                     "Если одобришь", "Если откажешь", "не запускает", "https://github.com"]:
            self.assertIn(part, t)
        texts = [b["text"] for row in s.sent[0]["buttons"] for b in row]
        self.assertEqual(texts, ["✅ Одобрить", "❌ Отклонить", "ℹ️ Подробнее"])

    def test_permission_not_grantable_in_telegram_gets_link_only(self):
        s = Sender()
        n = approval(kind="PERMISSION_REQUIRED", dedup_key="perm", button_safe=True)
        control.request(self.root, n, 1000, sender=s)
        self.assertEqual([[b["text"] for b in r] for r in s.sent[0]["buttons"]], [["ℹ️ Подробнее"]])
        self.assertIn("не в Telegram", s.sent[0]["text"])

    def test_unsafe_approval_has_no_decision_buttons(self):
        s = Sender()
        control.request(self.root, approval(button_safe=False), 1000, sender=s)
        self.assertEqual([[b["text"] for b in r] for r in s.sent[0]["buttons"]], [["ℹ️ Подробнее"]])

    def test_no_secrets_in_registry(self):
        control.request(self.root, approval(need="token " + ENV["TELEGRAM_BOT_TOKEN"]), 1000, sender=Sender())
        blob = ""
        for d, _, fs in os.walk(self.root):
            for f in fs:
                with open(os.path.join(d, f)) as fh:
                    blob += fh.read()
        self.assertNotIn(ENV["TELEGRAM_BOT_TOKEN"], blob)
        self.assertNotIn(CHAT, blob)


class Lifecycle(Base):
    def test_dedup_one_active_notification(self):
        s = Sender()
        self.assertTrue(control.request(self.root, approval(), 1000, sender=s)["sent"])
        r = control.request(self.root, approval(need="другой текст"), 1100, sender=s)
        self.assertTrue(r["duplicate"]); self.assertEqual(len(s.sent), 1)

    def test_single_reminder_then_silence(self):
        s = Sender()
        control.request(self.root, approval(), 0, sender=s)
        control.sweep(self.root, 29 * 60, sender=s); self.assertEqual(len(s.sent), 1)
        control.sweep(self.root, 31 * 60, sender=s); self.assertEqual(len(s.sent), 2)
        self.assertEqual(s.sent[1]["reply_to"], 101)
        self.assertIn("Напоминание", s.sent[1]["text"])
        for t in range(2, 40):
            control.sweep(self.root, t * 3600, sender=s)
        self.assertEqual(len(s.sent), 2)

    def test_resolved_gets_no_reminder_and_new_request_allowed(self):
        s = Sender()
        r = control.request(self.root, approval(), 0, sender=s)
        control.resolve(self.root, r["key_id"], 60, "chat")
        control.sweep(self.root, 3600, sender=s); self.assertEqual(len(s.sent), 1)
        self.assertTrue(control.request(self.root, approval(), 4000, sender=s)["sent"])

    def test_failed_delivery_is_not_lost(self):
        s = Sender(fail=1)
        r = control.request(self.root, approval(), 0, sender=s)
        self.assertFalse(r["sent"]); self.assertTrue(r["queued_for_retry"])
        self.assertEqual(control.load_note(self.root, r["key_id"])["status"], "queued")
        self.assertTrue(control.request(self.root, approval(), 10, sender=s)["duplicate"])   # still one
        out = control.sweep(self.root, 600, sender=s)
        self.assertEqual(out["retried"], 1); self.assertEqual(len(s.sent), 1)
        self.assertNotIn("Напоминание", s.sent[0]["text"])

    def test_long_outage_raises_fallback_alert_once(self):
        s = Sender(fail=10 ** 6)
        control.request(self.root, approval(), 0, sender=s)
        a = control.sweep(self.root, 7 * 3600, sender=s)["undelivered_alert"]
        b = control.sweep(self.root, 8 * 3600, sender=s)["undelivered_alert"]
        self.assertEqual(len(a), 1); self.assertEqual(b, [])

    def test_timeout_never_approves(self):
        s = Sender()
        r = control.request(self.root, approval(ttl_seconds=3600), 0, sender=s)
        control.sweep(self.root, 2 * 3600, sender=s)
        self.assertEqual(control.load_note(self.root, r["key_id"])["status"], "expired")
        self.assertFalse(os.path.exists(os.path.join(self.root, "decisions")))
        rec = control.load_note(self.root, r["key_id"])
        d = tg.callback_data(ENV["TELEGRAM_CALLBACK_SECRET"], "y", rec["rid"], CHAT)
        with open(os.path.join(self.root, "requests", rec["rid"] + ".json")) as fh:
            reg = json.load(fh)
        with self.assertRaises(tg.TgError):
            tg.decide(reg, None, ENV["TELEGRAM_CALLBACK_SECRET"], CHAT, d, CHAT, 2 * 3600)

    def test_button_decision_closes_request(self):
        s = Sender()
        import time
        now = time.time()
        r = control.request(self.root, approval(), now, sender=s)
        data = s.sent[0]["buttons"][0][0]["callback_data"]
        with mock.patch.object(tg, "call", return_value={"ok": True, "result": True}), \
             mock.patch("sys.stdout"):
            self.assertEqual(tg.main(["decide", "--data", data, "--from-id", CHAT, "--registry", self.root]), 0)
        self.assertEqual(control.load_note(self.root, r["key_id"])["status"], "resolved")
        control.sweep(self.root, now + 3600, sender=s); self.assertEqual(len(s.sent), 1)


if __name__ == "__main__":
    unittest.main()
