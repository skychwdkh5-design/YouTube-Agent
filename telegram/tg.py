#!/usr/bin/env python3
"""Telegram notifications for the YouTube-Agent automation (stdlib only).

The repository is PUBLIC: run logs and committed files are readable by anyone. Therefore
  * the bot token is read only from the TELEGRAM_BOT_TOKEN env var and scrubbed from every output;
  * the chat id is never printed or written to a file; it is masked in Actions logs and delivered
    only to the owner's own Telegram chat during pairing;
  * results written by the CLI (--out) contain only ok/error codes, message ids and the bot username.

Commands
  check                       token present? getMe works? webhook set? (no chat id needed)
  pair --code CODE            find the owner's "/start CODE" via getUpdates and DM them their chat id
  send-test                   send the fixed test message to TELEGRAM_CHAT_ID
  notify --kind K ...         video_ready | error | approval | info (approval adds signed buttons)
  decide ...                  validate a button press (used by telegram-decision.yml)

Nothing here sets a webhook, deletes a webhook or consumes updates (getUpdates is called without offset).
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

API = "https://api.telegram.org"
TEST_TEXT = "✅ Claude Control подключён к GitHub. Система уведомлений работает"
MAX_TEXT = 4096
RID_RE = re.compile(r"^[a-z0-9]{6,16}$")
ACTIONS = {"y": "approve", "n": "reject"}


class TgError(Exception):
    """An error whose message is already safe to print."""


# ---------- secrets hygiene ----------

def _secrets() -> list[str]:
    return [v for v in (os.environ.get("TELEGRAM_BOT_TOKEN", ""), os.environ.get("TELEGRAM_CHAT_ID", ""),
                        os.environ.get("TELEGRAM_CALLBACK_SECRET", "")) if len(v) >= 4]


def scrub(text: str, extra: list[str] | None = None) -> str:
    for s in _secrets() + (extra or []):
        if s and len(s) >= 4:
            text = text.replace(s, "***")
    # a bot token shape that slipped in from elsewhere
    return re.sub(r"\d{6,}:[A-Za-z0-9_-]{30,}", "***", text)


def mask_in_actions(value: str) -> None:
    if value and os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::add-mask::{value}", flush=True)


def token() -> str:
    t = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not t:
        raise TgError("TELEGRAM_BOT_TOKEN is empty or not available to this run")
    if not re.fullmatch(r"\d{5,}:[A-Za-z0-9_-]{30,}", t):
        raise TgError("TELEGRAM_BOT_TOKEN is present but does not look like a bot token (check for spaces/quotes)")
    return t


def chat_id() -> str:
    c = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not c:
        raise TgError("TELEGRAM_CHAT_ID secret is empty or missing - run pairing first and add the secret")
    if not re.fullmatch(r"-?\d{3,20}", c):
        raise TgError("TELEGRAM_CHAT_ID is present but is not a numeric chat id")
    mask_in_actions(c)
    return c


# ---------- Bot API ----------

def call(method: str, params: dict | None = None, timeout: int = 20) -> dict:
    """POST a Bot API method; returns the decoded JSON. Never lets the token reach an error message."""
    url = f"{API}/bot{token()}/{method}"
    data = json.dumps(params or {}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode())
        except Exception:
            body = {"ok": False, "error_code": e.code, "description": "HTTP error"}
    except Exception as e:  # network errors: report the class only
        raise TgError(f"network error calling {method}: {type(e).__name__}") from None
    if not body.get("ok"):
        raise TgError(scrub(f"{method} failed: {body.get('error_code')} {body.get('description', '')}"))
    return body


# ---------- signed buttons ----------

def sign(secret: str, action: str, rid: str, chat: str) -> str:
    mac = hmac.new(secret.encode(), f"v1|{action}|{rid}|{chat}".encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(mac).decode().rstrip("=")[:22]


def callback_data(secret: str, action: str, rid: str, chat: str) -> str:
    if action not in ACTIONS or not RID_RE.match(rid):
        raise TgError("bad action or request id")
    data = f"{action}:{rid}:{sign(secret, action, rid, chat)}"
    assert len(data.encode()) <= 64  # Telegram limit
    return data


def parse_callback(data: str) -> tuple[str, str, str]:
    parts = (data or "").split(":")
    if len(parts) != 3 or parts[0] not in ACTIONS or not RID_RE.match(parts[1]):
        raise TgError("malformed callback data")
    return parts[0], parts[1], parts[2]


def verify_callback(secret: str, data: str, chat: str) -> tuple[str, str]:
    action, rid, sig = parse_callback(data)
    if not hmac.compare_digest(sig, sign(secret, action, rid, chat)):
        raise TgError("bad signature")
    return action, rid


# ---------- messages ----------

def build_message(kind: str, title: str, body: str = "", url: str = "") -> str:
    head = {"video_ready": "🎬 Ролик готов", "error": "⚠️ Ошибка", "approval": "🟡 Нужно подтверждение", "info": "ℹ️ Статус"}.get(kind)
    if not head:
        raise TgError(f"unknown kind {kind}")
    lines = [f"{head}: {title}".strip()]
    if body:
        lines += ["", body]
    if url:
        lines += ["", url]
    text = scrub("\n".join(lines))
    return text if len(text) <= MAX_TEXT else text[: MAX_TEXT - 1] + "…"


def send(text: str, buttons: list[list[dict]] | None = None) -> dict:
    params = {"chat_id": chat_id(), "text": text, "disable_web_page_preview": True}
    if buttons:
        params["reply_markup"] = {"inline_keyboard": buttons}
    res = call("sendMessage", params)["result"]
    return {"ok": True, "message_id": res.get("message_id"), "date": res.get("date")}


# ---------- pairing ----------

def code_hash(code: str) -> str:
    return hashlib.sha256(code.strip().encode()).hexdigest()


def find_pair_chat(updates: list[dict], want_sha256: str) -> tuple[set[str], int]:
    """Private chats that sent '/start CODE' with sha256(CODE) == want_sha256 (only the hash is ever stored
    in the public repo). Returns (chat ids, number of other /start messages)."""
    found, other = set(), 0
    for u in updates:
        m = u.get("message") or {}
        text = (m.get("text") or "").strip()
        chat = m.get("chat") or {}
        if not text.startswith("/start") or chat.get("type") != "private":
            continue
        parts = text.split(maxsplit=1)
        if len(parts) == 2 and hmac.compare_digest(code_hash(parts[1]), want_sha256.lower()):
            found.add(str(chat.get("id")))
        else:
            other += 1
    return found, other


def cmd_check(_a) -> dict:
    me = call("getMe")["result"]
    wh = call("getWebhookInfo")["result"]
    url = wh.get("url") or ""
    host = re.sub(r"^https?://([^/]+).*$", r"\1", url) if url else ""
    return {"ok": True, "token_present": True, "bot_username": me.get("username"),
            "webhook_active": bool(url), "webhook_host": host, "pending_updates": wh.get("pending_update_count", 0)}


def cmd_pair(a) -> dict:
    want = (getattr(a, "code_sha256", None) or os.environ.get("PAIR_CODE_SHA256", "")).strip().lower()
    code = (getattr(a, "code", None) or os.environ.get("PAIR_CODE", "")).strip()
    if code:
        if not re.fullmatch(r"[A-Za-z0-9_-]{6,64}", code):
            raise TgError("pair code malformed")
        mask_in_actions(code)
        want = code_hash(code)
    if not re.fullmatch(r"[0-9a-f]{64}", want):
        raise TgError("pair code (or its sha256) missing")
    info = cmd_check(a)
    if info["webhook_active"]:
        return {**info, "paired": False, "reason": "webhook_active",
                "hint": "getUpdates is impossible while a webhook is set; not touching it (owner decision)"}
    ups = call("getUpdates", {"limit": 100, "timeout": 0, "allowed_updates": ["message"]})["result"]
    found, other = find_pair_chat(ups, want)
    out = {**info, "updates_seen": len(ups), "start_without_code": other}
    if len(found) != 1:
        return {**out, "paired": False, "reason": "no_match" if not found else "ambiguous"}
    cid = found.pop()
    mask_in_actions(cid)
    os.environ["TELEGRAM_CHAT_ID"] = cid  # for this process only, so send() and scrub() know it
    text = ("🔐 Привязка к GitHub-автоматизации\n\n"
            f"Твой chat_id: {cid}\n\n"
            "Добавь его в GitHub: Settings → Secrets and variables → Actions → New repository secret\n"
            "Name: TELEGRAM_CHAT_ID\nSecret: это число.\n\nНикому его не пересылай вместе с токеном бота.")
    res = call("sendMessage", {"chat_id": cid, "text": text})["result"]
    return {**out, "paired": True, "dm_message_id": res.get("message_id")}


def cmd_send_test(_a) -> dict:
    me = call("getMe")["result"]
    return {**send(TEST_TEXT), "bot_username": me.get("username"), "text": TEST_TEXT}


def cmd_notify(a) -> dict:
    text = build_message(a.kind, a.title, a.body or "", a.url or "")
    buttons = None
    if a.kind == "approval":
        secret = os.environ.get("TELEGRAM_CALLBACK_SECRET", "")
        if len(secret) < 32:
            raise TgError("approval buttons need TELEGRAM_CALLBACK_SECRET (>= 32 chars)")
        if not a.request_id:
            raise TgError("approval needs --request-id")
        c = chat_id()
        buttons = [[{"text": "✅ Одобрить", "callback_data": callback_data(secret, "y", a.request_id, c)},
                    {"text": "❌ Отклонить", "callback_data": callback_data(secret, "n", a.request_id, c)}]]
    return {**send(text, buttons), "kind": a.kind}


def decide(registry: dict | None, existing_decision: dict | None, secret: str, chat: str,
           data: str, from_id: str, now: float) -> dict:
    """Pure validation of one button press. Records a decision only; never triggers publishing."""
    if str(from_id) != str(chat):
        raise TgError("press from a foreign user")
    action, rid = verify_callback(secret, data, chat)
    if registry is None:
        raise TgError("unknown request id")
    if existing_decision is not None:
        raise TgError("already decided")
    if now > float(registry.get("expires_at", 0)):
        raise TgError("request expired")
    return {"request_id": rid, "decision": ACTIONS[action], "decided_at": int(now), "kind": registry.get("kind"),
            "note": "recorded only; does not authorize publishing"}


def _load(path: str):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def cmd_decide(a) -> dict:
    secret = os.environ.get("TELEGRAM_CALLBACK_SECRET", "")
    _, rid, _ = parse_callback(a.data)
    reg_p = os.path.join(a.registry, "requests", f"{rid}.json")
    dec_p = os.path.join(a.registry, "decisions", f"{rid}.json")
    reg = _load(reg_p)
    old = _load(dec_p)
    rec = decide(reg, old, secret, chat_id(), a.data, a.from_id, time.time())
    os.makedirs(os.path.dirname(dec_p), exist_ok=True)
    with open(dec_p, "w") as f:
        json.dump(rec, f, indent=1)
    return {"ok": True, **rec}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", help="write the (sanitized) result JSON here")
    sp = p.add_subparsers(dest="cmd", required=True)
    sp.add_parser("check")
    pp = sp.add_parser("pair"); pp.add_argument("--code"); pp.add_argument("--code-sha256")
    sp.add_parser("send-test")
    np_ = sp.add_parser("notify")
    np_.add_argument("--kind", required=True, choices=["video_ready", "error", "approval", "info"])
    np_.add_argument("--title", required=True); np_.add_argument("--body"); np_.add_argument("--url")
    np_.add_argument("--request-id")
    dp = sp.add_parser("decide")
    dp.add_argument("--data", required=True); dp.add_argument("--from-id", required=True)
    dp.add_argument("--registry", required=True)
    a = p.parse_args(argv)
    fn = {"check": cmd_check, "pair": cmd_pair, "send-test": cmd_send_test, "notify": cmd_notify, "decide": cmd_decide}[a.cmd]
    try:
        res, code = fn(a), 0
    except TgError as e:
        res, code = {"ok": False, "error": scrub(str(e))}, 1
    res = json.loads(scrub(json.dumps(res, ensure_ascii=False)))
    out = json.dumps(res, ensure_ascii=False, indent=1)
    print(out)
    if a.out:
        with open(a.out, "w") as f:
            f.write(out + "\n")
    if a.cmd == "pair" and not res.get("paired"):
        code = code or 2
    return code


if __name__ == "__main__":
    sys.exit(main())
