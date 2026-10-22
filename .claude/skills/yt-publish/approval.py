#!/usr/bin/env python3
"""approval.py - chat-to-publish approval records (schema yt-approval/1), stdlib only.

An approval is a small JSON record that binds ONE chat consent to exact content: the queue entry id, the file sha256, the title, the
description, thumbnail/caption hashes, flags and the publish time (all folded into `content_hash` / `entry_hash`). Change anything and the
hash changes, so the consent no longer matches. The workflow re-computes every hash from the pinned data commit before it touches YouTube.

    python3 approval.py card   --queue Q --id EP006 --root R            # what Claude shows the owner (card text + codes)
    python3 approval.py make   --queue Q --ids EP006 --label EP006 --quote "..." --scope single_release --queue-commit SHA --root R --out f.json
    python3 approval.py verify --approval f.json --queue Q --manifest M --root R --ledger L

Honest limit: the consent text is attested by Claude (chat messages are not cryptographically signed). The checks below make a mistaken or
ambiguous consent unable to publish anything other than what the card showed; the optional TOTP code (APPROVAL_TOTP_SECRET) adds real proof
that the owner was present for each release.
"""
import argparse, base64, hashlib, hmac, json, os, re, struct, sys, uuid
from datetime import datetime, timedelta, timezone

SCHEMA = "yt-approval/1"
MIN_LEAD, MAX_LEAD, TTL, MAX_PER_DAY = timedelta(minutes=30), timedelta(days=30), timedelta(hours=24), 8
AFFIRM = re.compile(r"одобря|подтвержда|\bapprove|\byes,?\s*publish|да,?\s*публику", re.I)
NEGATE = re.compile(r"\b(не|нет|no|not|don'?t|cancel|stop|стоп)\b|отмен|не\s*надо", re.I)


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def content_hash(e, root):
    """Everything about a release except WHEN: change any of it and an earlier consent stops matching."""
    obj = {k: e.get(k) for k in ("id", "kind", "title", "description", "tags", "category_id", "default_language", "made_for_kids",
                                  "contains_synthetic_media", "related")}
    obj["media_sha256"] = e["media"]["sha256"]
    th = e.get("thumbnail"); cap = e.get("captions") or {}
    obj["thumbnail_sha256"] = sha_file(os.path.join(root, th)) if th else None
    obj["captions_sha256"] = sha_file(os.path.join(root, cap["file"])) if cap.get("file") else None
    obj["captions_meta"] = {"language": cap.get("language"), "name": cap.get("name")} if cap else None
    return sha(canon(obj).encode())


def entry_hash(chash, publish_at):
    return sha(f"{chash}|{publish_at}".encode())


def parse_utc(s):
    t = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if t.tzinfo is None:
        raise ValueError("timezone missing")
    return t.astimezone(timezone.utc)


def consent_ok(quote, label):
    """The owner's own words must name the release and affirm it; questions, negations and other releases do not count."""
    q = (quote or "").strip()
    return bool(q) and label.lower() in q.lower() and bool(AFFIRM.search(q)) and not NEGATE.search(q) and not q.endswith("?")


def local_time(utc, tz="Asia/Ho_Chi_Minh"):
    try:
        from zoneinfo import ZoneInfo
        return utc.astimezone(ZoneInfo(tz))
    except Exception:
        return utc.astimezone(timezone(timedelta(hours=7)))


def card(e, root, tz="Asia/Ho_Chi_Minh"):
    ch = content_hash(e, root); eh = entry_hash(ch, e["publish_at"]); t = parse_utc(e["publish_at"])
    code = f"{eh[:4].upper()}-{eh[4:8].upper()}"
    text = "\n".join([
        f"APPROVAL CARD {code}", f"Release: {e['id']} ({e['kind']})", f"Title: {e['title']}",
        f"Publish: {local_time(t, tz):%a %Y-%m-%d %H:%M} {tz}  =  {t:%Y-%m-%d %H:%M} UTC",
        f"File sha256: {e['media']['sha256'][:16]}...  Thumbnail: {'yes' if e.get('thumbnail') else 'no'}  Captions: {'yes' if e.get('captions') else 'no'}",
        f"Not made for kids: {not e['made_for_kids']}  Altered/synthetic label: {e['contains_synthetic_media']}",
        "Upload: private + YouTube schedule (publishAt); it goes public by itself at the time above.",
        f"Consent must name '{e['id']}' (and may give the time). Any change to the release voids this card."])
    return {"card_text": text, "code": code, "content_hash": ch, "entry_hash": eh}


def make_record(entries, label, quote, scope, queue_commit, root, now=None, created_by="claude-chat"):
    now = now or datetime.now(timezone.utc)
    items = []
    for e in entries:
        ch = content_hash(e, root)
        items.append({"id": e["id"], "kind": e["kind"], "title": e["title"], "publish_at": e["publish_at"], "media_sha256": e["media"]["sha256"],
                      "content_hash": ch, "entry_hash": entry_hash(ch, e["publish_at"])})
    return {"schema": SCHEMA, "approval_id": uuid.uuid4().hex, "scope": scope, "label": label, "items": items, "queue_commit": queue_commit,
            "owner_quote": quote, "created_at": now.isoformat(timespec="seconds"), "expires_at": (now + TTL).isoformat(timespec="seconds"),
            "created_by": created_by}


def totp(secret_b32, t, step=30, digits=6):
    key = base64.b32decode(secret_b32.replace(" ", "").upper() + "=" * (-len(secret_b32) % 8))
    mac = hmac.new(key, struct.pack(">Q", int(t // step)), hashlib.sha1).digest()
    o = mac[-1] & 15
    return f"{(struct.unpack('>I', mac[o:o + 4])[0] & 0x7fffffff) % 10 ** digits:0{digits}d}"


def totp_check(secret, code, now, ledger):
    """Valid code within +-1 step, and each time-step is usable once (replay protection)."""
    ts = now.timestamp()
    for d in (0, -30, 30):
        if code and hmac.compare_digest(code.strip(), totp(secret, ts + d)):
            step = int((ts + d) // 30)
            if any(r.get("event") == "totp_used" and r.get("step") == step for r in ledger):
                return None, "one-time code already used"
            return step, None
    return None, "one-time code is wrong or expired"


def _state(ledger, digest):
    st = "none"
    for r in ledger:
        if r.get("sha256") == digest:
            st = {"started": "started", "uploaded": "uploaded", "abandoned": "none"}.get(r.get("event"), st)
    return st


def verify_record(rec, queue_items, manifest, root, ledger, now=None):
    now, pr = now or datetime.now(timezone.utc), []
    if rec.get("schema") != SCHEMA:
        return ["unknown approval schema"]
    try:
        created, expires = parse_utc(rec["created_at"]), parse_utc(rec["expires_at"])
    except (KeyError, ValueError):
        return ["approval timestamps missing or invalid"]
    if created > now + timedelta(minutes=2):
        pr.append("approval is dated in the future")
    if expires - created > TTL or now > expires:
        pr.append("approval expired (valid 24 h)" if now > expires else "approval lifetime exceeds 24 h")
    items, scope = rec.get("items") or [], rec.get("scope")
    if not items:
        pr.append("approval has no items")
    if scope == "single_release":
        if len(items) != 1 or items[0].get("kind") != "long":
            pr.append("a long video needs its own single-release approval")
    elif scope == "short_list":
        if any(i.get("kind") != "short" for i in items):
            pr.append("a Shorts list approval cannot include long videos")
    else:
        pr.append("unknown approval scope")
    if not consent_ok(rec.get("owner_quote"), rec.get("label", "")):
        pr.append("owner quote does not clearly approve this release (needs the release name, an approval, no negation or question)")
    if any(r.get("event") == "approval_done" and r.get("approval_id") == rec.get("approval_id") for r in ledger):
        pr.append("this approval was already executed")
    today = now.date().isoformat()
    if sum(1 for r in ledger if r.get("event") == "uploaded" and str(r.get("at", "")).startswith(today)) + len(items) > MAX_PER_DAY:
        pr.append(f"daily upload cap ({MAX_PER_DAY}) would be exceeded")
    by_id = {e["id"]: e for e in queue_items}
    sums = {f["asset"]: f["sha256"] for f in manifest.get("files", [])}
    for it in items:
        e = by_id.get(it.get("id"))
        if not e:
            pr.append(f"{it.get('id')}: not in the queue"); continue
        if e["kind"] != it.get("kind"):
            pr.append(f"{e['id']}: kind differs from the approval")
        if e.get("open_issues"):
            pr.append(f"{e['id']}: open issues in the queue entry")
        if e.get("title_status") != "final":
            pr.append(f"{e['id']}: title is not final")
        try:
            ch = content_hash(e, root)
        except OSError as ex:
            pr.append(f"{e['id']}: asset unreadable ({ex.filename})"); continue
        if ch != it.get("content_hash") or entry_hash(ch, e["publish_at"]) != it.get("entry_hash"):
            pr.append(f"{e['id']}: content or time changed since the approval")
        if e["title"] != it.get("title") or e["publish_at"] != it.get("publish_at"):
            pr.append(f"{e['id']}: title or publish time differs from the approval")
        if sums.get(e["media"]["asset"]) != e["media"]["sha256"] or e["media"]["sha256"] != it.get("media_sha256"):
            pr.append(f"{e['id']}: file sha256 differs from the approved one")
        try:
            lead = parse_utc(e["publish_at"]) - now
            if lead < MIN_LEAD or lead > MAX_LEAD:
                pr.append(f"{e['id']}: publish time must be 30 min to 30 days ahead")
        except ValueError:
            pr.append(f"{e['id']}: publish_at invalid")
        if _state(ledger, e["media"]["sha256"]) == "started":
            pr.append(f"{e['id']}: an earlier upload of this file is undetermined - reconcile first")
    return pr


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for n in ("card", "make", "verify"):
        s = sub.add_parser(n); s.add_argument("--queue", required=True); s.add_argument("--root", required=True)
    sub.choices["card"].add_argument("--id", required=True)
    m = sub.choices["make"]
    for k in ("ids", "label", "quote", "scope", "queue-commit", "out"):
        m.add_argument("--" + k, required=True)
    v = sub.choices["verify"]
    for k in ("approval", "manifest", "ledger"):
        v.add_argument("--" + k, required=True)
    a = p.parse_args(argv)
    items = json.load(open(a.queue))["items"]
    if a.cmd == "card":
        print(json.dumps(card(next(e for e in items if e["id"] == a.id), a.root), indent=1, ensure_ascii=False)); return 0
    if a.cmd == "make":
        want = a.ids.split(","); ents = [e for e in items if e["id"] in want]
        rec = make_record(ents, a.label, a.quote, a.scope, a.queue_commit, a.root)
        json.dump(rec, open(a.out, "w"), indent=1, ensure_ascii=False); print(json.dumps({"approval_id": rec["approval_id"], "out": a.out})); return 0
    led = [json.loads(x) for x in open(a.ledger) if x.strip()] if os.path.exists(a.ledger) else []
    probs = verify_record(json.load(open(a.approval)), items, json.load(open(a.manifest)), a.root, led)
    print(json.dumps({"ok": not probs, "problems": probs}, indent=1)); return 0 if not probs else 1


if __name__ == "__main__":
    sys.exit(main())
