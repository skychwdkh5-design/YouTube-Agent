"""APPROVAL ONLY / SILENT MODE for Telegram Control (owner policy, 2026-11-21).

Claude writes to the owner in Telegram ONLY when the owner personally has to act:
  APPROVAL_REQUIRED            - approve a video, a publication or another action;
  PERMISSION_REQUIRED          - an action needs the owner's permission;
  HUMAN_INTERVENTION_REQUIRED  - a blocker that cannot be removed safely and automatically.
Everything else (start, progress, render done, success, ordinary errors, publications, daily reports) is SUPPRESSED:
it is printed to the job log as "suppressed" and never sent.

Guarantees implemented here (pure logic + a file registry on branch telegram-data; tested in test_control.py):
  * gate():    a message is sent only if its kind is one of the three, all mandatory fields are filled, the caller
               states why Claude cannot continue, and (for blockers) which safe recovery was already tried.
               auto_resolvable=true -> suppressed. Unknown project -> refused.
  * dedup:     one open decision (dedup_key) = one active notification; repeats are dropped while it is open.
  * outbox:    the request is written to the registry BEFORE delivery; failed deliveries stay "queued" and are retried
               by the sweeper (every 10 min); after 6 h undelivered the workflow opens a GitHub issue as a fallback.
  * reminder:  exactly one reminder 30+ min after delivery if still open; then silence.
  * no timeout approvals: expiry only closes the request as "expired"; it never records a decision.
  * buttons:   Approve/Reject only for APPROVAL_REQUIRED with button_safe=true (signed, record-only);
               "Подробнее" is a link. Permissions that cannot be granted in Telegram get a link, no buttons.
               A press is recorded only and never starts publishing (CLAUDE.md chat-to-publish rules unchanged).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import time

import tg

KINDS = {
    "APPROVAL_REQUIRED": "🟡 Нужно твоё одобрение",
    "PERMISSION_REQUIRED": "🔑 Нужно твоё разрешение",
    "HUMAN_INTERVENTION_REQUIRED": "🛑 Нужно твоё вмешательство",
}
PROJECTS = {"OrbitalAtlas": "Orbital Atlas", "NEXORA": "NEXORA", "ANIMAVERSE": "ANIMAVERSE"}
REQUIRED = ("project", "need", "why_blocked", "on_approve", "on_reject", "dedup_key")
OPEN = {"queued", "sent", "reminded"}
REMIND_AFTER = 30 * 60
UNDELIVERED_ALERT_AFTER = 6 * 3600
DEFAULT_TTL = 7 * 24 * 3600
FIELD_MAX = 600


def gate(n: dict) -> tuple[bool, str]:
    """True only when the owner really has to act. The reason is printed for suppressed events."""
    kind = n.get("kind", "")
    if kind not in KINDS:
        return False, f"suppressed: kind '{kind or '-'}' does not need the owner (silent mode)"
    if n.get("auto_resolvable") is True:
        return False, "suppressed: caller says it can be resolved automatically within granted permissions"
    missing = [f for f in REQUIRED if not str(n.get(f, "")).strip()]
    if missing:
        return False, "refused: missing " + ", ".join(missing)
    if n["project"] not in PROJECTS:
        return False, f"refused: unknown project {n['project']}"
    if kind == "HUMAN_INTERVENTION_REQUIRED" and not str(n.get("recovery_attempted", "")).strip():
        return False, "refused: try safe automatic recovery first and describe it in recovery_attempted"
    if n.get("link") and not re.match(r"^https://", str(n["link"])):
        return False, "refused: link must be https"
    return True, "ok"


def _f(v) -> str:
    v = tg.scrub(str(v).strip())
    return v if len(v) <= FIELD_MAX else v[: FIELD_MAX - 1] + "…"


def buttons_allowed(n: dict) -> bool:
    return n["kind"] == "APPROVAL_REQUIRED" and n.get("button_safe") is True


def build_text(n: dict, reminder: bool = False) -> str:
    lines = []
    if reminder:
        lines += ["🔔 Напоминание (единственное): решение всё ещё ждёт тебя.", ""]
    lines += [f"{KINDS[n['kind']]}", "",
              f"Проект: {PROJECTS[n['project']]}",
              f"Что нужно от тебя: {_f(n['need'])}",
              f"Почему Claude не может продолжить сам: {_f(n['why_blocked'])}"]
    if n.get("recovery_attempted"):
        lines.append(f"Что уже пробовал: {_f(n['recovery_attempted'])}")
    yes, no = {"APPROVAL_REQUIRED": ("Если одобришь", "Если откажешь"),
               "PERMISSION_REQUIRED": ("Если разрешишь", "Если не разрешишь"),
               "HUMAN_INTERVENTION_REQUIRED": ("Когда сделаешь", "Если не сделать")}[n["kind"]]
    lines += [f"{yes}: {_f(n['on_approve'])}", f"{no}: {_f(n['on_reject'])}"]
    if n["kind"] == "PERMISSION_REQUIRED" and not buttons_allowed(n):
        lines.append("Разрешение даётся не в Telegram - открой ссылку ниже." if n.get("link")
                     else "Разрешение даётся не в Telegram - ответь Claude в исходной сессии.")
    if buttons_allowed(n):
        lines.append("Кнопка только записывает решение; публикацию она не запускает.")
    if n.get("link"):
        lines += ["", n["link"]]
    text = "\n".join(lines)
    return text if len(text) <= tg.MAX_TEXT else text[: tg.MAX_TEXT - 1] + "…"


def keyboard(n: dict, rid: str) -> list[list[dict]] | None:
    rows = []
    if buttons_allowed(n):
        secret = os.environ.get("TELEGRAM_CALLBACK_SECRET", "")
        if len(secret) < 32:
            raise tg.TgError("approval buttons need TELEGRAM_CALLBACK_SECRET (>= 32 chars)")
        c = tg.chat_id()
        rows.append([{"text": "✅ Одобрить", "callback_data": tg.callback_data(secret, "y", rid, c)},
                     {"text": "❌ Отклонить", "callback_data": tg.callback_data(secret, "n", rid, c)}])
    if n.get("link"):
        rows.append([{"text": "ℹ️ Подробнее", "url": n["link"]}])
    return rows or None


# ---------- registry (branch telegram-data, checked out at `root`) ----------

def key_id(dedup_key: str) -> str:
    return hashlib.sha256(dedup_key.strip().encode()).hexdigest()[:16]


def _p(root, *parts):
    return os.path.join(root, *parts)


def _read(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def _write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)


def load_note(root, kid):
    return _read(_p(root, "notifications", f"{kid}.json"))


def save_note(root, note):
    _write(_p(root, "notifications", f"{note['key_id']}.json"), note)


def deliver(note: dict, now: float, reminder: bool = False, sender=None) -> bool:
    """One delivery attempt with short in-process retries. Updates note; never raises on delivery failure."""
    sender = sender or _send
    n = note["request"]
    note["attempts"] = note.get("attempts", 0) + 1
    try:
        res = sender(build_text(n, reminder), keyboard(n, note["rid"]),
                     note.get("message_id") if reminder else None)
    except tg.TgError as e:
        note["last_error"] = tg.scrub(str(e))[:300]
        return False
    if reminder:
        note.update(status="reminded", reminded_at=int(now))
    else:
        note.update(status="sent", sent_at=int(now), message_id=res.get("message_id"))
    note.pop("last_error", None)
    return True


def _send(text, buttons, reply_to):
    params = {"chat_id": tg.chat_id(), "text": text, "disable_web_page_preview": True}
    if buttons:
        params["reply_markup"] = {"inline_keyboard": buttons}
    if reply_to:
        params["reply_parameters"] = {"message_id": reply_to, "allow_sending_without_reply": True}
    last = None
    for i in range(3):
        try:
            return tg.call("sendMessage", params)["result"]
        except tg.TgError as e:
            last = e
            if " 400 " in f" {e} " or " 403 " in f" {e} ":   # bad request / blocked: retrying will not help now
                break
            time.sleep(min(2 ** i * 2, 10))
    raise last


def request(root: str, n: dict, now: float, sender=None) -> dict:
    ok, reason = gate(n)
    if not ok:
        return {"ok": True, "sent": False, "suppressed": reason.startswith("suppressed"), "reason": reason}
    kid = key_id(n["dedup_key"])
    old = load_note(root, kid)
    if old and old.get("status") in OPEN:
        return {"ok": True, "sent": False, "duplicate": True, "key_id": kid, "status": old["status"],
                "reason": "one open decision = one active notification"}
    rid = secrets.token_hex(6)
    ttl = int(n.get("ttl_seconds") or DEFAULT_TTL)
    clean = {k: (tg.scrub(str(v)) if isinstance(v, str) else v) for k, v in n.items()}
    note = {"key_id": kid, "rid": rid, "status": "queued", "created_at": int(now), "expires_at": int(now) + ttl,
            "attempts": 0, "request": clean}
    # outbox first: the request survives a delivery failure or a crashed run
    _write(_p(root, "requests", f"{rid}.json"),
           {"kind": n["kind"], "key_id": kid, "created_at": int(now), "expires_at": int(now) + ttl})
    save_note(root, note)
    delivered = deliver(note, now, sender=sender)
    save_note(root, note)
    return {"ok": True, "sent": delivered, "queued_for_retry": not delivered, "key_id": kid, "rid": rid}


def sweep(root: str, now: float, sender=None) -> dict:
    """Retry queued deliveries, send the single 30-min reminder, close expired requests. Never decides anything."""
    out = {"retried": 0, "reminded": 0, "expired": 0, "undelivered_alert": []}
    d = _p(root, "notifications")
    for name in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        note = _read(_p(d, name))
        st = note.get("status")
        if st not in OPEN:
            continue
        if now >= note.get("expires_at", 0):
            note.update(status="expired", closed_at=int(now))   # no decision is recorded on timeout
            out["expired"] += 1
        elif st == "queued":
            if deliver(note, now, sender=sender):
                out["retried"] += 1
            elif now - note["created_at"] >= UNDELIVERED_ALERT_AFTER and not note.get("alerted"):
                note["alerted"] = int(now)
                out["undelivered_alert"].append(note["key_id"])
        elif st == "sent" and now - note.get("sent_at", now) >= REMIND_AFTER:
            if deliver(note, now, reminder=True, sender=sender):
                out["reminded"] += 1
        save_note(root, note)
    return {"ok": True, **out}


def resolve(root: str, kid: str, now: float, how: str) -> dict:
    note = load_note(root, kid)
    if not note:
        raise tg.TgError("unknown notification")
    if note["status"] in OPEN:
        note.update(status="resolved", closed_at=int(now), resolved_by=how)
        save_note(root, note)
    return {"ok": True, "key_id": kid, "status": note["status"], "message_id": note.get("message_id")}
