#!/usr/bin/env python3
"""engine.py - state of one daily release, from plan to a verified YouTube schedule. Stdlib only, no network.

A release is one JSON file (schema pipeline-release/1) under <state>/releases/<id>.json. Every stage writes what it produced
(paths + sha256) so a restart continues from the last finished stage instead of redoing (and re-paying for) earlier ones.

Lifecycle (long video):
    planned -> scripted -> voiced -> rendered -> qc_passed -> preview_requested -> preview_ready -> card_shown
            -> approved -> schedule_requested -> scheduled (verified on YouTube)
    side states: needs_changes (owner pressed "На правку"), blocked (credentials/limits; resumes at the saved stage), dropped

The approval rules the owner set on 2026-11-19 (replacing the "Одобряю ep0NN" phrase for pipeline releases):
  * one card per release version; "ок" (button or text) from the owner's account approves exactly that card;
  * a new video / cover / title / description / captions = a new version: every open card of the old version is void;
  * an expired card, a card that is not the latest for its release, a repeated answer or an answer from anyone else never
    schedules anything; a bare "ок" that could mean more than one open card is ambiguous and is not bound to any of them;
  * the owner's "ок" schedules the approved version at the card's slot; nothing becomes public immediately.
"""
import hashlib, json, os, re, uuid
from datetime import datetime, date, time, timedelta, timezone

SCHEMA = "pipeline-release/1"
HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "config", "channels.json")

STAGES = ["planned", "scripted", "voiced", "rendered", "qc_passed", "preview_requested", "preview_ready", "card_shown",
          "approved", "schedule_requested", "scheduled"]
TERMINAL = {"scheduled", "dropped"}
VERSION_FIELDS = ("video_sha256", "thumbnail_sha256", "captions_sha256", "title", "description", "tags")


class PipelineError(Exception):
    pass


# --- basics ---------------------------------------------------------------------------------------------------------

def load_config(path=CONFIG):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def utcnow():
    return datetime.now(timezone.utc)


def iso(t):
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse(s):
    t = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if t.tzinfo is None:
        raise PipelineError(f"time without zone: {s}")
    return t.astimezone(timezone.utc)


def tzinfo(name="Asia/Ho_Chi_Minh"):
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(name)
    except Exception:                                   # Asia/Ho_Chi_Minh has no DST: UTC+7 is exact
        return timezone(timedelta(hours=7))


def local(t, cfg):
    return t.astimezone(tzinfo(cfg.get("timezone", "Asia/Ho_Chi_Minh")))


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# --- schedule: which channel produces today -------------------------------------------------------------------------

def production_channel(day, cfg):
    """The owner's rotation: day index from the epoch, even -> first channel, odd -> second."""
    ep = date.fromisoformat(cfg["rotation"]["epoch"])
    order = cfg["rotation"]["order"]
    return order[(day - ep).days % len(order)]


def today_local(cfg, now=None):
    return local(now or utcnow(), cfg).date()


# --- release files --------------------------------------------------------------------------------------------------

def rel_path(state, rid):
    if not re.fullmatch(r"[a-z]{2}-\d{8}-\d{2}", rid):
        raise PipelineError(f"bad release id {rid!r}")
    return os.path.join(state, "releases", rid + ".json")


def load(state, rid):
    with open(rel_path(state, rid), encoding="utf-8") as f:
        return json.load(f)


def save(state, rel, now=None):
    rel["updated_at"] = iso(now or utcnow())
    p = rel_path(state, rel["id"])
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rel, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, p)                                    # atomic: a crash never leaves half a state file
    return p


def all_releases(state):
    d = os.path.join(state, "releases")
    out = []
    if os.path.isdir(d):
        for n in sorted(os.listdir(d)):
            if n.endswith(".json"):
                with open(os.path.join(d, n), encoding="utf-8") as f:
                    out.append(json.load(f))
    return out


def log(rel, event, now=None, **kw):
    rel.setdefault("events", []).append({"at": iso(now or utcnow()), "event": event, **kw})


def new_release(state, channel, cfg, day=None, kind="long", topic=None, now=None, test=False):
    """Create the next release of a production day. Refuses to create a duplicate while the channel has an unfinished one.
    A test release (ids NN >= 90) never counts as a duplicate, never holds a slot and can never be scheduled for real."""
    now = now or utcnow()
    day = day or today_local(cfg, now)
    if channel not in cfg["channels"]:
        raise PipelineError(f"unknown channel {channel}")
    open_ = [r for r in all_releases(state) if r["channel"] == channel and r["kind"] == kind and r["stage"] not in TERMINAL
             and not r.get("test")]
    limit = cfg["channels"][channel].get("long_per_production_day", 1) if kind == "long" else 99
    if len(open_) >= limit and not test:
        raise PipelineError(f"{channel} already has unfinished {kind} release(s) {[r['id'] for r in open_]} - continue those instead of starting a duplicate")
    if topic and not test:
        for r in all_releases(state):
            if r["channel"] == channel and topic_similar((r.get("topic") or {}).get("title", ""), topic.get("title", "")):
                raise PipelineError(f"topic already used by {r['id']}")
    n = 90 if test else 1
    while os.path.exists(rel_path(state, f"{cfg['channels'][channel]['release_prefix']}-{day:%Y%m%d}-{n:02d}")):
        n += 1
    rid = f"{cfg['channels'][channel]['release_prefix']}-{day:%Y%m%d}-{n:02d}"
    rel = {"schema": SCHEMA, "id": rid, "channel": channel, "kind": kind, "production_day": day.isoformat(), "stage": "planned",
           "topic": topic or {}, "artifacts": {}, "versions": [], "cards": [], "approval": None, "preview": None, "schedule": None,
           "blocker": None, "created_at": iso(now), "events": [], "test": bool(test)}
    log(rel, "created", now, channel=channel, production_day=day.isoformat())
    save(state, rel, now)
    return rel


STOP = {"from", "with", "that", "this", "what", "when", "where", "which", "here", "there", "they", "their", "then", "than", "into",
        "over", "under", "after", "before", "about", "orbit", "space", "satellite", "satellites", "nasa", "why", "how", "just"}


def topic_words(title):
    return {w for w in re.findall(r"[a-z0-9]{3,}", (title or "").lower()) if w not in STOP}


def topic_similar(a, b, threshold=0.6):
    """Two topic titles about the same thing (word overlap of the meaningful words)."""
    wa, wb = topic_words(a), topic_words(b)
    if not wa or not wb:
        return False
    return len(wa & wb) / min(len(wa), len(wb)) >= threshold


# --- stages ---------------------------------------------------------------------------------------------------------

def stage_index(stage):
    return STAGES.index(stage) if stage in STAGES else -1


def record_stage(rel, stage, artifacts=None, now=None, **info):
    """Mark a production stage done with its artifacts. Going back (a re-render) is allowed only through new_version()."""
    if stage not in ("scripted", "voiced", "rendered", "qc_passed"):
        raise PipelineError(f"record_stage does not handle {stage}")
    if rel["stage"] in ("approved", "schedule_requested", "scheduled"):
        raise PipelineError(f"{rel['id']} is {rel['stage']}: production stages are closed - start a new version")
    rel["artifacts"][stage] = {"at": iso(now or utcnow()), **(artifacts or {}), **info}
    if stage_index(stage) > stage_index(rel["stage"]) or rel["stage"] in ("needs_changes", "blocked"):
        rel["stage"] = stage
    rel["blocker"] = None
    log(rel, "stage_done", now, stage=stage)


def resume_point(rel):
    """The first stage that still has to run (what a restart after a crash does next)."""
    if rel["stage"] == "blocked":
        return rel["blocker"].get("resume_at") if rel.get("blocker") else "planned"
    order = ["scripted", "voiced", "rendered", "qc_passed"]
    for s in order:
        if s not in rel["artifacts"]:
            return s
    if not rel.get("preview") or not rel["preview"].get("video_id"):
        return "preview"
    if rel["stage"] in ("preview_ready", "needs_changes"):
        return "card"
    return {"card_shown": "await_owner", "approved": "schedule", "schedule_requested": "schedule_result",
            "scheduled": "done", "dropped": "done"}.get(rel["stage"], "card")


def block(rel, reason, resume_at, now=None):
    """Credentials revoked, voice limit reached, sources missing... Keep everything finished, remember where to resume.
    Returns True only the first time this reason blocks the release (-> send ONE notification, not one per retry)."""
    b = rel.get("blocker") or {}
    first = rel["stage"] != "blocked" or b.get("reason") != reason
    prev = b.get("prev_stage") if rel["stage"] == "blocked" else rel["stage"]
    rel["blocker"] = {"reason": reason, "resume_at": resume_at, "since": b.get("since") if not first else iso(now or utcnow()),
                      "prev_stage": prev}
    rel["stage"] = "blocked"
    if first:
        log(rel, "blocked", now, reason=reason, resume_at=resume_at)
    return first


def unblock(rel, now=None):
    b = rel.get("blocker") or {}
    rel["stage"] = b.get("prev_stage", "planned")
    rel["blocker"] = None
    log(rel, "unblocked", now)


# --- versions and cards ---------------------------------------------------------------------------------------------

def version_hash(v):
    return sha_text(canon({k: v.get(k) for k in VERSION_FIELDS}))


def new_version(rel, *, video_sha256, thumbnail_sha256, captions_sha256, title, description, tags, duration_s, files, now=None):
    """Register what the owner will be shown. Any change of video, cover, title, description, tags or captions makes a new
    version and voids every open card of the previous one."""
    now = now or utcnow()
    v = {"video_sha256": video_sha256, "thumbnail_sha256": thumbnail_sha256, "captions_sha256": captions_sha256, "title": title,
         "description": description, "tags": list(tags), "duration_s": round(float(duration_s), 1), "files": files}
    h = version_hash(v)
    cur = current_version(rel)
    if cur and cur["version_hash"] == h:
        return cur, False
    if rel["stage"] in ("schedule_requested", "scheduled"):
        raise PipelineError(f"{rel['id']} is already {rel['stage']} - a scheduled video is never replaced automatically")
    v.update({"n": len(rel["versions"]) + 1, "version_hash": h, "created_at": iso(now)})
    rel["versions"].append(v)
    for c in rel["cards"]:
        if c.get("status") == "open":
            c["status"] = "void"
            c["void_reason"] = f"replaced by version {v['n']}"
    if rel.get("approval") and rel["approval"].get("version_hash") != h:
        rel["approval"]["status"] = "void"
    rel["preview"] = None                               # a new file needs its own private preview
    if stage_index(rel["stage"]) > stage_index("qc_passed") or rel["stage"] == "needs_changes":
        rel["stage"] = "qc_passed" if "qc_passed" in rel["artifacts"] else "rendered"
    log(rel, "version", now, n=v["n"], version_hash=h[:12])
    return v, True


def current_version(rel):
    return rel["versions"][-1] if rel["versions"] else None


def card_code(card_id):
    return card_id.split("-", 1)[1].upper()


def make_card(rel, cfg, slot_utc, now=None, message_id=None):
    """One approval card for the current version + its preview. Showing a new card voids the older open ones."""
    now = now or utcnow()
    v = current_version(rel)
    if not v:
        raise PipelineError("no version to show")
    if rel["stage"] not in ("preview_ready", "card_shown", "needs_changes"):
        raise PipelineError(f"{rel['id']} is {rel['stage']}: a card needs a QC-passed version with a private preview")
    pv = rel.get("preview") or {}
    if pv.get("version_hash") != v["version_hash"] or not pv.get("video_id"):
        raise PipelineError("the private preview does not belong to the current version")
    lead = timedelta(minutes=cfg["card"]["min_lead_minutes"])
    if slot_utc - now < lead + timedelta(minutes=5):
        raise PipelineError("slot too close: pick a later slot")
    for c in rel["cards"]:
        if c.get("status") == "open":
            c["status"] = "void"
            c["void_reason"] = "superseded by a newer card"
    cid = f"card-{uuid.uuid4().hex[:8]}"
    expires = min(now + timedelta(hours=cfg["card"]["ttl_hours"]), slot_utc - lead)
    c = {"card_id": cid, "code": card_code(cid), "release": rel["id"], "version": v["n"], "version_hash": v["version_hash"],
         "video_id": pv["video_id"], "slot": iso(slot_utc), "shown_at": iso(now), "expires_at": iso(expires), "status": "open",
         "message_id": message_id}
    rel["cards"].append(c)
    rel["stage"] = "card_shown"
    log(rel, "card", now, card_id=cid, version=v["n"], slot=c["slot"])
    return c


def card_text(rel, card, cfg):
    v = next(x for x in rel["versions"] if x["n"] == card["version"])
    ch = cfg["channels"][rel["channel"]]
    t = parse(card["slot"])
    mins, secs = divmod(int(round(v["duration_s"])), 60)
    return "\n".join([
        f"**{ch['name']} · {rel['id']} · v{v['n']}** (карточка {card['code']})",
        f"**{v['title']}**",
        f"Длительность: {mins}:{secs:02d}",
        f"Слот: {local(t, cfg):%a %d.%m %H:%M} ({cfg['timezone']}) = {t:%Y-%m-%d %H:%M} UTC",
        f"Посмотреть (закрытое видео на канале): https://youtu.be/{card['video_id']}",
        f"Карточка действует до {local(parse(card['expires_at']), cfg):%d.%m %H:%M}."])


# --- the owner's answer -------------------------------------------------------------------------------------------

def is_ok_text(text, cfg):
    q = (text or "").strip().lower().strip(".! ")
    if not q or len(q) > 60 or "?" in q or re.search(r"\b(не|нет|no|not|stop|стоп|отмен)", q):
        return False
    words = set(re.findall(r"[\wё]+", q))
    return bool(words & set(cfg["card"]["ok_words"]))


def open_cards(releases, now):
    out = []
    for r in releases:
        for c in r["cards"]:
            if c.get("status") == "open" and parse(c["expires_at"]) > now:
                out.append((r, c))
    return out


def decide(releases, cfg, *, choice, actor, now=None, card_id=None, comment=None, source=None, message_id=None):
    """Apply the owner's answer. Returns {"result": ..., ...}; only result == "approved" leads to scheduling.

    choice: "ok" or "changes". actor: "<trust>:<name>" of whoever answered (must be in owner.approval_actors).
    card_id: the card the answer belongs to (a button press always carries it; a text reply may not)."""
    now = now or utcnow()
    if actor not in cfg["owner"]["approval_actors"]:
        return {"result": "rejected", "reason": f"answer from {actor!r}, not from the owner's account"}
    if choice not in ("ok", "changes"):
        return {"result": "rejected", "reason": f"unknown choice {choice!r}"}
    if card_id is None:
        cands = open_cards(releases, now)
        if len(cands) != 1:
            return {"result": "ambiguous" if cands else "no_open_card",
                    "candidates": [{"release": r["id"], "card_id": c["card_id"], "title": next(v["title"] for v in r["versions"] if v["n"] == c["version"])}
                                   for r, c in cands]}
        card_id = cands[0][1]["card_id"]
    hit = [(r, c) for r in releases for c in r["cards"] if c["card_id"] == card_id]
    if not hit:
        return {"result": "rejected", "reason": f"unknown card {card_id}"}
    rel, c = hit[0]
    if c.get("status") == "decided":
        d = c.get("decision") or {}
        return {"result": "duplicate", "release": rel["id"], "card_id": card_id, "earlier": d.get("choice"),
                "approval_id": (rel.get("approval") or {}).get("approval_id"), "reason": "this card was already answered - nothing new is done"}
    if c.get("status") == "void":
        return {"result": "rejected", "release": rel["id"], "card_id": card_id, "reason": f"card is void ({c.get('void_reason')})"}
    if parse(c["expires_at"]) <= now:
        c["status"] = "expired"
        log(rel, "card_expired_answer", now, card_id=card_id)
        return {"result": "expired", "release": rel["id"], "card_id": card_id, "reason": "card expired - a new card with a new slot is needed"}
    latest = [x for x in rel["cards"] if x.get("status") in ("open", "decided")][-1:]
    v = current_version(rel)
    if not latest or latest[0]["card_id"] != card_id or c["version_hash"] != v["version_hash"]:
        c["status"] = "void"
        c["void_reason"] = "not the latest card of the current version"
        return {"result": "rejected", "release": rel["id"], "card_id": card_id, "reason": c["void_reason"]}
    c["status"] = "decided"
    c["decision"] = {"choice": choice, "actor": actor, "at": iso(now), "comment": comment, "source": source, "message_id": message_id}
    if choice == "changes":
        rel["stage"] = "needs_changes"
        rel.setdefault("change_requests", []).append({"at": iso(now), "card_id": card_id, "comment": comment or ""})
        log(rel, "changes_requested", now, card_id=card_id)
        return {"result": "changes", "release": rel["id"], "card_id": card_id, "comment": comment or ""}
    appr = {"approval_id": uuid.uuid4().hex, "release": rel["id"], "channel": rel["channel"], "card_id": card_id, "card_code": c["code"],
            "version": c["version"], "version_hash": c["version_hash"], "video_sha256": v["video_sha256"], "video_id": c["video_id"],
            "publish_at": c["slot"], "actor": actor, "approved_at": iso(now), "source": source, "message_id": message_id,
            "status": "valid", "single_use": True, "test": bool(rel.get("test"))}
    rel["approval"] = appr
    rel["stage"] = "approved"
    log(rel, "approved", now, card_id=card_id, approval_id=appr["approval_id"])
    return {"result": "approved", "release": rel["id"], "card_id": card_id, "approval": appr}


# --- slots ----------------------------------------------------------------------------------------------------------

def slot_candidates(cfg, channel, kind, now, days=30):
    ch = cfg["channels"][channel]
    tz = tzinfo(cfg["timezone"])
    start = local(now, cfg).date()
    for d in range(days + 1):
        day = start + timedelta(days=d)
        for hm in ch["slots"].get(kind, []):
            h, m = map(int, hm.split(":"))
            yield datetime.combine(day, time(h, m), tz).astimezone(timezone.utc)


def busy_days(cfg, inventory, releases, channel, kind):
    """Local days already holding a long (or short) release: scheduled or published videos on the channel (YouTube is the
    truth), plus releases of this pipeline that hold a slot (an open card, an approval or a schedule)."""
    out = set()
    for v in inventory or []:
        if kind == "long" and (v.get("seconds") or 0) <= 180 and v.get("seconds") is not None:
            continue
        if kind == "short" and (v.get("seconds") or 999) > 180:
            continue
        t = v.get("publishAt") or (v.get("publishedAt") if v.get("privacy") == "public" else None)
        if t:
            out.add((local(parse(t), cfg).date(), local(parse(t), cfg).strftime("%H:%M")))
    for r in releases:
        if r["channel"] != channel or r["kind"] != kind or r.get("test"):
            continue
        held = []
        if r.get("schedule") and r["schedule"].get("publish_at"):
            held.append(r["schedule"]["publish_at"])
        if r.get("approval") and r["approval"].get("status") == "valid":
            held.append(r["approval"]["publish_at"])
        held += [c["slot"] for c in r["cards"] if c.get("status") == "open"]
        for t in held:
            out.add((local(parse(t), cfg).date(), local(parse(t), cfg).strftime("%H:%M")))
    return out


def pick_slot(cfg, channel, kind, inventory, releases, now=None, min_lead=timedelta(hours=3), exclude_release=None):
    """Nearest free slot at least `min_lead` ahead (time for the owner to watch and answer)."""
    now = now or utcnow()
    rels = [r for r in releases if r["id"] != exclude_release]
    busy = busy_days(cfg, inventory, rels, channel, kind)
    for t in slot_candidates(cfg, channel, kind, now):
        if t - now < min_lead:
            continue
        lt = local(t, cfg)
        if kind == "long" and any(d == lt.date() for d, _ in busy):
            continue                                     # one long video per channel per day
        if (lt.date(), lt.strftime("%H:%M")) in busy:
            continue
        return t
    raise PipelineError("no free slot in the next 30 days")


# --- requests for the YouTube side (GitHub Actions) ------------------------------------------------------------------

def preview_request(rel, cfg, meta):
    """What the ops workflow needs to upload the current version as a PRIVATE preview (no publishAt)."""
    v = current_version(rel)
    return {"op": "preview", "release": rel["id"], "channel": rel["channel"], "channel_id": cfg["channels"][rel["channel"]]["channel_id"],
            "version": v["n"], "version_hash": v["version_hash"], "video_sha256": v["video_sha256"], "title": v["title"],
            "description": v["description"], "tags": v["tags"], "thumbnail_sha256": v["thumbnail_sha256"],
            "captions_sha256": v["captions_sha256"], "files": v["files"], "category_id": meta.get("category_id", "28"),
            "default_language": "en", "made_for_kids": bool(meta.get("made_for_kids", False)),
            "contains_synthetic_media": bool(meta.get("contains_synthetic_media", False)),
            "marker_tag": f"pipeline-{rel['id']}-v{v['n']}"}


def schedule_request(rel, cfg):
    a = rel.get("approval")
    if not a or a.get("status") != "valid" or rel["stage"] not in ("approved", "schedule_requested"):
        raise PipelineError(f"{rel['id']}: no valid approval to schedule")
    v = current_version(rel)
    if a["version_hash"] != v["version_hash"] or (rel.get("preview") or {}).get("video_id") != a["video_id"]:
        raise PipelineError("approval does not match the current version / preview")
    return {"op": "schedule", "release": rel["id"], "channel": rel["channel"], "channel_id": cfg["channels"][rel["channel"]]["channel_id"],
            "approval": a, "video_id": a["video_id"], "publish_at": a["publish_at"], "version_hash": a["version_hash"],
            "video_sha256": a["video_sha256"], "made_for_kids": False,
            "contains_synthetic_media": bool((rel.get("meta") or {}).get("contains_synthetic_media", False)),
            "test": bool(rel.get("test"))}


def apply_preview_result(rel, res, now=None):
    v = current_version(rel)
    if res.get("video_sha256") != v["video_sha256"]:
        raise PipelineError("preview result is for another file")
    if not res.get("ok"):
        log(rel, "preview_failed", now, error=res.get("error"))
        return False
    rel["preview"] = {"video_id": res["video_id"], "version": v["n"], "version_hash": v["version_hash"], "at": iso(now or utcnow()),
                      "privacy": res.get("privacyStatus"), "url": f"https://youtu.be/{res['video_id']}"}
    rel["stage"] = "preview_ready"
    log(rel, "preview_ready", now, video_id=res["video_id"])
    return True


def apply_schedule_result(rel, res, now=None):
    a = rel.get("approval") or {}
    if res.get("approval_id") != a.get("approval_id"):
        raise PipelineError("schedule result is for another approval")
    if res.get("ok"):
        rel["schedule"] = {"video_id": res["video_id"], "publish_at": res["publishAt"], "privacy": res.get("privacyStatus"),
                           "verified_at": iso(now or utcnow()), "url": f"https://youtu.be/{res['video_id']}"}
        rel["stage"] = "scheduled"
        a["status"] = "used"
        log(rel, "scheduled", now, video_id=res["video_id"], publish_at=res["publishAt"])
        return True
    log(rel, "schedule_failed", now, error=res.get("error"), kind=res.get("error_kind"))
    if res.get("error_kind") == "slot_taken":
        a["status"] = "void"
        rel["stage"] = "preview_ready"                    # needs a new card with a new slot; nothing was changed on YouTube
    return False
