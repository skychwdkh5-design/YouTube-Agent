#!/usr/bin/env python3
"""One-line Telegram silent-mode hooks for production workflows (Orbital Atlas, NEXORA, ANIMAVERSE).

Every command: checks out the registry (branch telegram-data of $GITHUB_REPOSITORY), runs the silent-mode gate
(control.py), commits the registry back, and ALWAYS exits 0 - a notification problem must never fail a production job.
Only situations where the owner must act produce a message; everything else is logged as suppressed.

  ask ...                         one explicit request (fields as in control.REQUIRED)
  resolve --dedup KEY             close an open request (no reminder)
  sweep [--fallback-issue]        retries, the single 30-min reminder, expiry
  scan-auth --project P FILE...   YouTube OAuth dead (invalid_grant / refresh failed / secret missing) -> HUMAN_INTERVENTION
  scan-yt-release FILE            YouTube-Agent release_check JSON: issue opened -> ask; public/rescheduled -> resolve
  scan-nx-release FILE            NEXORA release_check log: "-> issue" -> ask; "public (confirmed" -> resolve
  scan-pipeline DIR               pipeline-ops results: error_kind auth -> ask (quota/ordinary errors stay silent)
  from-file FILE                  {"op":"resolve","dedup_key":K} or an ask object (Claude sessions via telegram-ops)
  check                           secrets present? bot reachable? (sends nothing)
After a new request is delivered or queued, a repository_dispatch "telegram_remind" starts telegram-remind.yml
(30-min reminder / retry), because GitHub cron schedules can run hours late.
Env: GITHUB_TOKEN or GH_TOKEN, GITHUB_REPOSITORY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID[, TELEGRAM_CALLBACK_SECRET].
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import control  # noqa: E402
import tg  # noqa: E402

AUTH_RE = re.compile(r"invalid_grant|token refresh failed|unauthorized_client|NEXORA_YT_[A-Z_]+ is not set|YT_[A-Z_]+ is not set")
PROJECT_LABEL = {"OrbitalAtlas": "Orbital Atlas", "NEXORA": "NEXORA", "ANIMAVERSE": "ANIMAVERSE"}


def run_url() -> str:
    s, r, i = os.environ.get("GITHUB_SERVER_URL", "https://github.com"), os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_RUN_ID", "")
    return f"{s}/{r}/actions/runs/{i}" if r and i else ""


# ---------- registry checkout / save ----------

def _git(cwd, *args, check=True):
    return subprocess.run(["git", *args], cwd=cwd, check=check, capture_output=True, text=True)


def open_registry() -> str | None:
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    d = tempfile.mkdtemp(prefix="tgreg-")
    if not tok or not repo:          # local / test use: plain directory
        return d
    _git(d, "init", "-q", "-b", "telegram-data")
    _git(d, "remote", "add", "origin", f"https://x-access-token:{tok}@github.com/{repo}.git")
    if _git(d, "fetch", "-q", "origin", "telegram-data", check=False).returncode == 0:
        _git(d, "checkout", "-q", "-f", "FETCH_HEAD", "-B", "telegram-data")
    _git(d, "config", "user.name", "github-actions[bot]")
    _git(d, "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    return d


def save_registry(d: str, msg: str) -> None:
    if not os.path.isdir(os.path.join(d, ".git")):
        return
    if not _git(d, "status", "--porcelain").stdout.strip():
        return
    _git(d, "add", "-A")
    _git(d, "commit", "-q", "-m", msg)
    for i in range(5):
        if _git(d, "push", "-q", "origin", "HEAD:telegram-data", check=False).returncode == 0:
            return
        _git(d, "pull", "-q", "--rebase", "origin", "telegram-data", check=False)
        time.sleep(3 * (i + 1))
    print("WARNING: registry push failed (notification state kept only in this run)")


# ---------- request builders ----------

def auth_request(project: str, reason: str) -> dict:
    p = PROJECT_LABEL[project]
    return {"kind": "HUMAN_INTERVENTION_REQUIRED", "project": project,
            "need": f"Заново подключить доступ к YouTube для канала {p} (вход в Google)",
            "why_blocked": "Google отклоняет сохранённый доступ к каналу; новый вход может сделать только владелец аккаунта",
            "recovery_attempted": f"Ошибка не сетевая, повтор не помогает: {reason}",
            "on_approve": "После нового входа загрузки, расписание и проверки релизов продолжатся сами",
            "on_reject": "Загрузки, расписание и проверки релизов этого канала остаются на паузе",
            "dedup_key": f"{project}/youtube-oauth", "link": run_url()}


def release_request(project: str, rid: str, video_id: str, publish_at: str, status: str) -> dict:
    return {"kind": "HUMAN_INTERVENTION_REQUIRED", "project": project,
            "need": f"Проверить в YouTube Studio ролик {rid}: в назначенное время ({publish_at}) он не стал публичным",
            "why_blocked": "Claude не меняет видимость и время уже загруженных роликов - это решение владельца",
            "recovery_attempted": f"Проверка повторялась каждые 15 минут; статус сейчас: {status}",
            "on_approve": "Если сделаешь ролик публичным или назначишь новое время, проверка подтвердит это сама",
            "on_reject": "Ролик останется непубличным",
            "dedup_key": f"{project}/release/{rid}",
            "link": f"https://studio.youtube.com/video/{video_id}/edit" if re.fullmatch(r"[\w-]{6,20}", video_id or "") else run_url()}


# ---------- scanners (pure, tested) ----------

def scan_auth_text(text: str) -> str | None:
    m = AUTH_RE.search(text or "")
    return m.group(0) if m else None


def scan_yt_release(data: dict) -> tuple[list[dict], list[str]]:
    asks, resolves = [], []
    for it in data.get("items", []) if isinstance(data, dict) else []:
        a = it.get("action", "")
        if a in ("release_confirmed", "release_rescheduled"):
            resolves.append(f"OrbitalAtlas/release/{it.get('id')}")
        elif a == "still not public" and it.get("issue"):
            st = it.get("privacyStatus") or ("видео не найдено" if not it.get("found", True) else "неизвестно")
            asks.append(release_request("OrbitalAtlas", it["id"], it.get("video_id", ""), it.get("publishAt", ""), st))
    return asks, resolves


NX_ISSUE = re.compile(r"^\s+(\S+): (\S+) (\d+) min after publishAt -> issue")
NX_OK = re.compile(r"^\s+(\S+): public \(confirmed")
NX_VID = re.compile(r"^\s+(\d\d\.\d\d \d\d:\d\d ICT)\s+(\S+)\s+(\S+)")


def scan_nx_release(text: str) -> tuple[list[dict], list[str]]:
    vids = {m.group(2): (m.group(3), m.group(1)) for m in map(NX_VID.match, text.splitlines()) if m}
    asks, resolves = [], []
    for line in text.splitlines():
        if (m := NX_ISSUE.match(line)):
            vid, when = vids.get(m.group(1), ("", "?"))
            asks.append(release_request("NEXORA", m.group(1), vid, when, m.group(2)))
        elif (m := NX_OK.match(line)):
            resolves.append(f"NEXORA/release/{m.group(1)}")
    return asks, resolves


def scan_pipeline(results: list[dict], project: str = "OrbitalAtlas") -> list[dict]:
    for r in results:
        if not r.get("ok") and r.get("error_kind") == "auth":
            return [auth_request(project, str(r.get("error", ""))[:160])]
    return []


# ---------- execution ----------

def execute(asks: list[dict], resolves: list[str], label: str, do_sweep=False, fallback_issue=False) -> dict:
    if not asks and not resolves and not do_sweep:
        print("telegram: nothing that needs the owner (silent)")
        return {"ok": True}
    reg = open_registry()
    now, out = time.time(), {"asks": [], "resolved": []}
    for key in resolves:
        kid = control.key_id(key)
        note = control.load_note(reg, kid)
        if note and note.get("status") in control.OPEN:
            r = control.resolve(reg, kid, now, "auto:" + label)
            try:
                tg._drop_buttons(r.get("message_id"))
            except Exception:
                pass
            out["resolved"].append(key)
    for n in asks:
        try:
            out["asks"].append(control.request(reg, n, now))
        except Exception as e:  # never break production
            out["asks"].append({"ok": False, "error": tg.scrub(str(e))[:200]})
    if do_sweep:
        s = control.sweep(reg, now)
        out["sweep"] = s
        if fallback_issue and s.get("undelivered_alert"):
            subprocess.run(["gh", "issue", "create", "-R", os.environ.get("GITHUB_REPOSITORY", ""), "--title", "Telegram: решение ждёт тебя, но не доставлено",
                            "--body", "Telegram не принимает сообщения 6+ часов. Открытые запросы (key_id): "
                            + ", ".join(s["undelivered_alert"]) + f". Branch telegram-data, notifications/. Run: {run_url()}"],
                           check=False)
    save_registry(reg, f"telegram {label} {os.environ.get('GITHUB_RUN_ID', '')}".strip())
    if any(a.get("sent") or a.get("queued_for_retry") for a in out["asks"]):
        out["remind_dispatched"] = dispatch_remind()
    return {"ok": True, **out}


def dispatch_remind() -> bool:
    """Start telegram-remind.yml in this repo (GITHUB_TOKEN-made repository_dispatch does trigger workflows)."""
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not tok or not repo:
        return False
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/dispatches", method="POST",
                                 data=json.dumps({"event_type": "telegram_remind"}).encode(),
                                 headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json",
                                          "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 204
    except Exception:
        return False


def check() -> dict:
    out = {"bot_token_present": bool(os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()),
           "chat_id_present": bool(os.environ.get("TELEGRAM_CHAT_ID", "").strip())}
    try:
        out["bot_username"] = tg.call("getMe")["result"].get("username")
        out["bot_reachable"] = True
        tg.chat_id()
        out["chat_id_valid"] = True
    except tg.TgError as e:
        out["error"] = tg.scrub(str(e))
    out["ok"] = bool(out.get("bot_reachable") and out.get("chat_id_valid"))
    return out


def _read(path):
    try:
        with open(path) as f:
            return f.read()
    except OSError:
        return ""


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    a_ = sp.add_parser("ask")
    for f in ("kind", "project", "need", "why_blocked", "on_approve", "on_reject", "dedup_key"):
        a_.add_argument("--" + f.replace("_", "-"), required=True)
    a_.add_argument("--recovery-attempted", default=""); a_.add_argument("--link", default="")
    a_.add_argument("--button-safe", action="store_true")
    r_ = sp.add_parser("resolve"); r_.add_argument("--dedup", required=True)
    s_ = sp.add_parser("sweep"); s_.add_argument("--fallback-issue", action="store_true")
    au = sp.add_parser("scan-auth"); au.add_argument("--project", required=True, choices=list(PROJECT_LABEL)); au.add_argument("files", nargs="*")
    yr = sp.add_parser("scan-yt-release"); yr.add_argument("file")
    nr = sp.add_parser("scan-nx-release"); nr.add_argument("file")
    pl = sp.add_parser("scan-pipeline"); pl.add_argument("dir"); pl.add_argument("--project", default="OrbitalAtlas")
    ff = sp.add_parser("from-file"); ff.add_argument("file")
    sp.add_parser("check")
    a = p.parse_args(argv)
    try:
        if a.cmd == "ask":
            n = {k: getattr(a, k) for k in ("kind", "project", "need", "why_blocked", "on_approve", "on_reject",
                                            "dedup_key", "recovery_attempted", "link")}
            n["button_safe"] = a.button_safe
            res = execute([n], [], "ask")
        elif a.cmd == "resolve":
            res = execute([], [a.dedup], "resolve")
        elif a.cmd == "sweep":
            res = execute([], [], "sweep", do_sweep=True, fallback_issue=a.fallback_issue)
        elif a.cmd == "scan-auth":
            hit = next((h for h in (scan_auth_text(_read(f)) for f in a.files) if h), None)
            res = execute([auth_request(a.project, hit)] if hit else [], [], "auth")
        elif a.cmd == "scan-yt-release":
            txt = _read(a.file)
            try:
                data = json.loads(txt)
            except ValueError:
                data = {}
            asks, resolves = scan_yt_release(data)
            hit = scan_auth_text(txt)
            if hit:
                asks.append(auth_request("OrbitalAtlas", hit))
            res = execute(asks, resolves, "release-check")
        elif a.cmd == "check":
            res = check()
        elif a.cmd == "from-file":
            obj = json.loads(_read(a.file) or "{}")
            if obj.get("op") == "resolve":
                res = execute([], [str(obj.get("dedup_key", ""))], "resolve")
            else:
                res = execute([obj], [], "session-ask")
        elif a.cmd == "scan-nx-release":
            txt = _read(a.file)
            asks, resolves = scan_nx_release(txt)
            hit = scan_auth_text(txt)
            if hit:
                asks.append(auth_request("NEXORA", hit))
            res = execute(asks, resolves, "release-check")
        else:
            rs = []
            for f in glob.glob(os.path.join(a.dir, "*.json")):
                try:
                    rs.append(json.loads(_read(f)))
                except ValueError:
                    pass
            res = execute(scan_pipeline(rs, a.project), [], "pipeline")
    except Exception as e:   # a notification problem must never fail production
        res = {"ok": False, "error": tg.scrub(f"{type(e).__name__}: {e}")[:300]}
    print(tg.scrub(json.dumps(res, ensure_ascii=False)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
