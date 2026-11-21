import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

sys.path.insert(0, os.path.dirname(__file__))
import tg  # noqa: E402

FAKE_TOKEN = "123456789:AAFakeFakeFakeFakeFakeFakeFakeFake12"
SECRET = "s" * 40


class Hygiene(unittest.TestCase):
    def test_scrub_token_and_shape(self):
        with mock.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": FAKE_TOKEN}):
            self.assertNotIn(FAKE_TOKEN, tg.scrub(f"url /bot{FAKE_TOKEN}/getMe"))
        self.assertNotIn("AAFake", tg.scrub(f"x {FAKE_TOKEN} y"))

    def test_missing_token(self):
        with mock.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": ""}):
            with self.assertRaises(tg.TgError):
                tg.token()

    def test_bad_token_shape(self):
        with mock.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": '"' + FAKE_TOKEN + '"'}):
            with self.assertRaises(tg.TgError):
                tg.token()

    def test_error_output_never_contains_token(self):
        def boom(*a, **k):
            raise tg.TgError(f"getMe failed: 401 Unauthorized {FAKE_TOKEN}")
        with mock.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": FAKE_TOKEN}), mock.patch.object(tg, "call", boom):
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = tg.main(["check"])
        self.assertEqual(rc, 1)
        self.assertNotIn(FAKE_TOKEN, buf.getvalue())


class Buttons(unittest.TestCase):
    def test_roundtrip_and_length(self):
        d = tg.callback_data(SECRET, "y", "ep015abc", "987654321")
        self.assertLessEqual(len(d.encode()), 64)
        self.assertEqual(tg.verify_callback(SECRET, d, "987654321"), ("y", "ep015abc"))

    def test_tamper(self):
        d = tg.callback_data(SECRET, "n", "ep015abc", "987654321")
        with self.assertRaises(tg.TgError):
            tg.verify_callback(SECRET, "y" + d[1:], "987654321")   # flip reject -> approve
        with self.assertRaises(tg.TgError):
            tg.verify_callback(SECRET, d, "111111111")             # other chat
        with self.assertRaises(tg.TgError):
            tg.verify_callback("x" * 40, d, "987654321")           # other secret

    def test_decide_rules(self):
        chat = "987654321"
        d = tg.callback_data(SECRET, "y", "ep015abc", chat)
        reg = {"kind": "approval", "expires_at": 2000}
        rec = tg.decide(reg, None, SECRET, chat, d, chat, 1000)
        self.assertEqual(rec["decision"], "approve")
        self.assertIn("does not authorize publishing", rec["note"])
        for args in [(reg, {"x": 1}, d, chat, 1000),   # replay
                     (reg, None, d, chat, 3000),       # expired
                     (None, None, d, chat, 1000),      # unknown
                     (reg, None, d, "5", 1000)]:       # foreign user
            with self.assertRaises(tg.TgError):
                tg.decide(args[0], args[1], SECRET, chat, args[2], args[3], args[4])

    def test_decide_cli_writes_once(self):
        chat = "987654321"
        d = tg.callback_data(SECRET, "n", "req123abc", chat)
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(f"{tmp}/requests")
            with open(f"{tmp}/requests/req123abc.json", "w") as f:
                json.dump({"kind": "approval", "expires_at": 9e12}, f)
            env = {"TELEGRAM_CALLBACK_SECRET": SECRET, "TELEGRAM_CHAT_ID": chat}
            with mock.patch.dict(os.environ, env), redirect_stdout(io.StringIO()):
                self.assertEqual(tg.main(["decide", "--data", d, "--from-id", chat, "--registry", tmp]), 0)
                self.assertEqual(tg.main(["decide", "--data", d, "--from-id", chat, "--registry", tmp]), 1)


class Pairing(unittest.TestCase):
    def upd(self, text, cid=42, typ="private"):
        return {"message": {"text": text, "chat": {"id": cid, "type": typ}}}

    def test_only_exact_code_private(self):
        ups = [self.upd("/start ABC123xyz", 42), self.upd("/start", 7), self.upd("/start WRONG000", 8),
               self.upd("/start ABC123xyz", 9, "group")]
        found, other = tg.find_pair_chat(ups, tg.code_hash("ABC123xyz"))
        self.assertEqual(found, {"42"})
        self.assertEqual(other, 2)

    def test_webhook_blocks_pairing(self):
        with mock.patch.object(tg, "cmd_check", lambda a: {"ok": True, "webhook_active": True}), \
             mock.patch.object(tg, "call") as c:
            res = tg.cmd_pair(mock.Mock(code="ABC123xyz", code_sha256=None))
        self.assertFalse(res["paired"])
        c.assert_not_called()   # no getUpdates, no deleteWebhook

    def test_pair_result_has_no_chat_id(self):
        calls = []

        def fake_call(method, params=None):
            calls.append(method)
            if method == "getUpdates":
                return {"result": [self.upd("/start ABC123xyz", 5550001111)]}
            return {"result": {"message_id": 7}}
        with mock.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": FAKE_TOKEN, "GITHUB_ACTIONS": ""}), \
             mock.patch.object(tg, "cmd_check", lambda a: {"ok": True, "webhook_active": False}), \
             mock.patch.object(tg, "call", fake_call):
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = tg.main(["pair", "--code-sha256", tg.code_hash("ABC123xyz")])
            os.environ.pop("TELEGRAM_CHAT_ID", None)
        self.assertEqual(rc, 0)
        self.assertNotIn("5550001111", buf.getvalue())
        self.assertNotIn("deleteWebhook", calls)
        self.assertNotIn("setWebhook", calls)


if __name__ == "__main__":
    unittest.main()
