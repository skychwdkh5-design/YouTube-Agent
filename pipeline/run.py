#!/usr/bin/env python3
"""run.py - command line for the daily release pipeline (used by the scheduled Claude session and by people).

State lives on the data branch `publish-data` under pipeline/ (releases/*.json). Check it out once as a worktree:
    git worktree add ../pipeline-data origin/publish-data      # then --state ../pipeline-data/pipeline (default below)

    python3 pipeline/run.py today                                    # which channel produces today, unfinished releases, resume points
    python3 pipeline/run.py new --channel oa --topic topic.json      # refuses duplicates and repeated topics
    python3 pipeline/run.py stage --release R --stage voiced --artifacts '{"voice": "...", "voice_sha256": "..."}'
    python3 pipeline/run.py version --release R --video V.mp4 --thumbnail T.jpg --captions C.srt --meta meta.json
    python3 pipeline/run.py media-branch --release R --dir /tmp/mb   # files for the private preview upload (parts + request)
    python3 pipeline/run.py preview-result --release R --result results/x.json
    python3 pipeline/run.py slot --release R --status results/status-....json
    python3 pipeline/run.py card --release R --slot 2026-11-21T01:00:00Z [--message-id cmsg_...]
    python3 pipeline/run.py decide --choice ok --actor "principal:Егор" [--card card-xxxx] [--comment ...] [--source ...]
    python3 pipeline/run.py schedule-request --release R --out pipeline-ops/requests/schedule-R.json [--confirm]
    python3 pipeline/run.py schedule-result --release R --result results/schedule-R.json
    python3 pipeline/run.py block --release R --reason "..." --resume-at voiced | unblock --release R
Every command prints JSON.
"""
import argparse, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import engine as E  # noqa: E402

DEFAULT_STATE = os.environ.get("PIPELINE_STATE", os.path.abspath(os.path.join(HERE, "..", "..", "pipeline-data", "pipeline")))
PART = 45 * 1024 * 1024


def out(o):
    print(json.dumps(o, indent=1, ensure_ascii=False))


def ffprobe_duration(path):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(p.stdout.strip())


def cmd_today(a, cfg):
    now = E.utcnow()
    day = E.today_local(cfg, now)
    rels = E.all_releases(a.state)
    open_ = [{"id": r["id"], "channel": r["channel"], "stage": r["stage"], "resume": E.resume_point(r),
              "blocker": r.get("blocker"), "title": (E.current_version(r) or {}).get("title") or r.get("topic", {}).get("title")}
             for r in rels if r["stage"] not in E.TERMINAL]
    ch = E.production_channel(day, cfg)
    return {"local_date": day.isoformat(), "production_channel": ch, "channel_name": cfg["channels"][ch]["name"],
            "open_releases": open_, "open_cards": [{"release": r["id"], "card_id": c["card_id"], "expires_at": c["expires_at"]}
                                                    for r, c in E.open_cards(rels, now)],
            "start_new": not any(o["channel"] == ch for o in open_)}


def cmd_new(a, cfg):
    topic = json.load(open(a.topic)) if a.topic else None
    r = E.new_release(a.state, a.channel, cfg, topic=topic)
    return {"created": r["id"], "stage": r["stage"]}


def cmd_stage(a, cfg):
    r = E.load(a.state, a.release)
    E.record_stage(r, a.stage, json.loads(a.artifacts or "{}"))
    E.save(a.state, r)
    return {"release": r["id"], "stage": r["stage"], "resume": E.resume_point(r)}


def cmd_version(a, cfg):
    r = E.load(a.state, a.release)
    meta = json.load(open(a.meta))
    files = {"video": os.path.abspath(a.video), "thumbnail": os.path.abspath(a.thumbnail), "captions": os.path.abspath(a.captions)}
    v, new = E.new_version(r, video_sha256=E.sha_file(a.video), thumbnail_sha256=E.sha_file(a.thumbnail),
                           captions_sha256=E.sha_file(a.captions), title=meta["title"], description=meta["description"],
                           tags=meta.get("tags", []), duration_s=ffprobe_duration(a.video), files=files)
    r["meta"] = {k: meta[k] for k in ("category_id", "made_for_kids", "contains_synthetic_media") if k in meta}
    E.save(a.state, r)
    return {"release": r["id"], "version": v["n"], "new": new, "version_hash": v["version_hash"], "stage": r["stage"]}


def cmd_media_branch(a, cfg):
    """Prepare the orphan branch content for the private preview upload: file parts, SHA256SUMS, request.json, workflow."""
    r = E.load(a.state, a.release)
    if r["stage"] not in ("qc_passed", "preview_requested", "needs_changes"):
        raise E.PipelineError(f"{r['id']} is {r['stage']}: a preview needs a QC-passed version")
    v = E.current_version(r)
    req = E.preview_request(r, cfg, r.get("meta", {}))
    req["confirm"] = bool(a.confirm)
    req["name"] = f"preview-{r['id']}-v{v['n']}" + ("" if a.confirm else "-dry")
    os.makedirs(a.dir, exist_ok=True)
    sums = []
    for k in ("video", "thumbnail", "captions"):
        src = v["files"][k]
        name = os.path.basename(src)
        with open(src, "rb") as f:
            i = 0
            while True:
                b = f.read(PART)
                if not b:
                    break
                with open(os.path.join(a.dir, f"{name}.part{i:02d}"), "wb") as g:
                    g.write(b)
                i += 1
        sums.append(f"{E.sha_file(src)}  {name}")
    with open(os.path.join(a.dir, "SHA256SUMS"), "w") as f:
        f.write("\n".join(sums) + "\n")
    with open(os.path.join(a.dir, "request.json"), "w") as f:
        json.dump(req, f, ensure_ascii=False, indent=1)
    wf = os.path.join(a.dir, ".github", "workflows")
    os.makedirs(wf, exist_ok=True)
    shutil.copy(os.path.join(HERE, "..", ".github", "workflows", "pipeline-ops.yml"), wf)
    r["stage"] = "preview_requested"
    E.log(r, "preview_requested", branch=f"pipeline-media/{r['id']}-v{v['n']}", confirm=bool(a.confirm))
    E.save(a.state, r)
    return {"release": r["id"], "branch": f"pipeline-media/{r['id']}-v{v['n']}", "dir": a.dir, "request": req["name"]}


def cmd_preview_result(a, cfg):
    r = E.load(a.state, a.release)
    res = json.load(open(a.result))
    ok = E.apply_preview_result(r, res)
    E.save(a.state, r)
    return {"release": r["id"], "ok": ok, "stage": r["stage"], "preview": r.get("preview"), "error": res.get("error"), "error_kind": res.get("error_kind")}


def cmd_slot(a, cfg):
    r = E.load(a.state, a.release)
    st = json.load(open(a.status)) if a.status else {"videos": []}
    if a.status and not st.get("ok"):
        raise E.PipelineError(f"channel status unavailable: {st.get('error')}")
    t = E.pick_slot(cfg, r["channel"], r["kind"], st.get("videos", []), E.all_releases(a.state), exclude_release=r["id"])
    return {"release": r["id"], "slot": E.iso(t), "local": f"{E.local(t, cfg):%Y-%m-%d %H:%M} {cfg['timezone']}"}


def cmd_card(a, cfg):
    r = E.load(a.state, a.release)
    c = E.make_card(r, cfg, E.parse(a.slot), message_id=a.message_id)
    E.save(a.state, r)
    return {"card": c, "text": E.card_text(r, c, cfg)}


def cmd_card_message(a, cfg):
    r = E.load(a.state, a.release)
    c = next(x for x in r["cards"] if x["card_id"] == a.card)
    c["message_id"] = a.message_id
    E.save(a.state, r)
    return {"card_id": c["card_id"], "message_id": a.message_id}


def cmd_decide(a, cfg):
    rels = E.all_releases(a.state)
    res = E.decide(rels, cfg, choice=a.choice, actor=a.actor, card_id=a.card, comment=a.comment, source=a.source, message_id=a.message_id)
    for r in rels:                                          # persist whatever the decision changed (card status, approval)
        E.save(a.state, r)
    return res


def cmd_schedule_request(a, cfg):
    r = E.load(a.state, a.release)
    req = E.schedule_request(r, cfg)
    req["confirm"] = bool(a.confirm)
    req["name"] = os.path.basename(a.out)[:-5]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(req, f, ensure_ascii=False, indent=1)
    if a.confirm:
        r["stage"] = "schedule_requested"
        E.log(r, "schedule_requested", approval_id=req["approval"]["approval_id"], request=req["name"])
        E.save(a.state, r)
    return {"release": r["id"], "request": a.out, "confirm": bool(a.confirm), "publish_at": req["publish_at"]}


def cmd_schedule_result(a, cfg):
    r = E.load(a.state, a.release)
    res = json.load(open(a.result))
    if res.get("dry_run"):
        return {"release": r["id"], "dry_run": True, "ok": res.get("ok"), "already_done": res.get("already_done")}
    ok = E.apply_schedule_result(r, res)
    E.save(a.state, r)
    return {"release": r["id"], "ok": ok, "stage": r["stage"], "schedule": r.get("schedule"), "error": res.get("error"), "error_kind": res.get("error_kind")}


def cmd_block(a, cfg):
    r = E.load(a.state, a.release)
    notify = E.block(r, a.reason, a.resume_at)
    E.save(a.state, r)
    return {"release": r["id"], "stage": r["stage"], "notify_owner": notify}


def cmd_unblock(a, cfg):
    r = E.load(a.state, a.release)
    E.unblock(r)
    E.save(a.state, r)
    return {"release": r["id"], "stage": r["stage"], "resume": E.resume_point(r)}


def cmd_show(a, cfg):
    return E.load(a.state, a.release)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--state", default=DEFAULT_STATE)
    s = p.add_subparsers(dest="cmd", required=True)
    s.add_parser("today")
    x = s.add_parser("new"); x.add_argument("--channel", required=True); x.add_argument("--topic")
    x = s.add_parser("stage"); x.add_argument("--release", required=True); x.add_argument("--stage", required=True); x.add_argument("--artifacts")
    x = s.add_parser("version")
    for k in ("release", "video", "thumbnail", "captions", "meta"):
        x.add_argument("--" + k, required=True)
    x = s.add_parser("media-branch"); x.add_argument("--release", required=True); x.add_argument("--dir", required=True); x.add_argument("--confirm", action="store_true")
    x = s.add_parser("preview-result"); x.add_argument("--release", required=True); x.add_argument("--result", required=True)
    x = s.add_parser("slot"); x.add_argument("--release", required=True); x.add_argument("--status")
    x = s.add_parser("card"); x.add_argument("--release", required=True); x.add_argument("--slot", required=True); x.add_argument("--message-id")
    x = s.add_parser("card-message"); x.add_argument("--release", required=True); x.add_argument("--card", required=True); x.add_argument("--message-id", required=True)
    x = s.add_parser("decide"); x.add_argument("--choice", required=True, choices=["ok", "changes"]); x.add_argument("--actor", required=True)
    x.add_argument("--card"); x.add_argument("--comment"); x.add_argument("--source"); x.add_argument("--message-id")
    x = s.add_parser("schedule-request"); x.add_argument("--release", required=True); x.add_argument("--out", required=True); x.add_argument("--confirm", action="store_true")
    x = s.add_parser("schedule-result"); x.add_argument("--release", required=True); x.add_argument("--result", required=True)
    x = s.add_parser("block"); x.add_argument("--release", required=True); x.add_argument("--reason", required=True); x.add_argument("--resume-at", required=True)
    x = s.add_parser("unblock"); x.add_argument("--release", required=True)
    x = s.add_parser("show"); x.add_argument("--release", required=True)
    a = p.parse_args(argv)
    cfg = E.load_config()
    fn = globals()["cmd_" + a.cmd.replace("-", "_")]
    try:
        out(fn(a, cfg))
        return 0
    except (E.PipelineError, FileNotFoundError, KeyError, ValueError) as ex:
        out({"status": "error", "error": str(ex)})
        return 1


if __name__ == "__main__":
    sys.exit(main())
