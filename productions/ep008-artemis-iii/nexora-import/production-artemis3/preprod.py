#!/usr/bin/env python3
"""Artemis III pre-production: timeline, second-by-second edit map, temp captions, nx-scenes plan.

    python3 preprod.py                # reads voice_temp/lines.json (temporary local voice, NOT for release)

Writes (all derived, re-run after any script/voice change):
  edit_plan_shots.csv   one row per shot: in/out, visual, asset slot or graphic, on-screen text, claims
  edit_plan.csv         one row per second: what is on screen, what is said, which asset
  captions_temp.srt     phrase captions from measured temp-voice line lengths (re-time on the final voice)
  scenes.json           nx-scenes plan (photo scenes point at assets/<slot>.jpg - empty until originals arrive)
  timeline_summary.json totals, slot usage, hook timing
Prints JSON. Never downloads, renders or publishes anything.
"""
import csv, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP_LINE, GAP_SCENE = 0.30, 0.80          # breath between lines / extra beat at a scene change
PHOTO, GRAPHIC = "photo", "graphic"

# Asset slots: NASA originals the owner supplies (ASSETS_NEEDED.md). Credit is drawn on screen.
SLOTS = {
    "n1-boosters": ("NASA/Cory S Huston", "SLS twin boosters get nose cones, VAB High Bay 3, 2026-09-30"),
    "n2-orion": ("NASA/Amanda Stevenson", "Artemis III Orion crew + service modules joined, 2026-07-30/31"),
    "n3-rs25": ("NASA/Ben Smegelsky", "Four RS-25 engines for Artemis III at the VAB, 2026-07-21"),
    "n4-conops": ("NASA", "Artemis III concept of operations graphic (NASA), 2026-10-23"),
    "n5-solar": ("NASA/Amanda Stevenson", "Artemis III Orion solar array wing inspection, 2026-08-18"),
    "n6-booster-rpsf": ("NASA/Ben Smegelsky", "Right center booster on a work stand, RPSF, 2026-07-22"),
}

# scene id -> (visual kind, slot or graphic name, on-screen text, camera/notes, hold after VO in s)
SHOTS = {
    "h1-boosters": (PHOTO, "n1-boosters", "", "tilt up base -> nose cones; no insignia legible", 0.0),
    "h2-leo": (GRAPHIC, "g-leo-card", "LOW EARTH ORBIT · 2027", "Earth-limb line art, orbit ring draws; label 'NEXORA GRAPHIC'", 0.0),
    "h3-conops": (PHOTO, "n4-conops", "NASA PLAN · OCT 23, 2026", "push-in on the NASA graphic; on-screen 'NASA CONCEPT GRAPHIC'", 0.0),
    "h4-two-landers": (GRAPHIC, "g-two-landers", "2 LANDERS · 2 COMPANIES · 1 SPACECRAFT", "kinetic stack; no company artwork", 0.4),
    "p1-title": (GRAPHIC, "g-chapter-1", "WHAT CHANGED", "chapter card", 0.8),
    "p1-feb": (GRAPHIC, "g-timeline", "FEB 27, 2026 → ARTEMIS III = EARTH ORBIT · ARTEMIS IV = LANDING, 2028", "date timeline animates left->right; source line NASA 2026-02-27", 0.3),
    "p1-why": (PHOTO, "n2-orion", "", "slow push-in", 0.3),
    "p1-quote": (GRAPHIC, "g-quote", "\"Keep testing like we fly\" - Amit Kshatriya, NASA", "quote card with source NASA 2026-02-27", 0.3),
    "p1-hardware": (PHOTO, "n3-rs25", "", "3 photos in rhythm: n3-rs25 -> n2-orion -> n1-boosters (one per sentence)", 0.3),
    "p2-crew": (GRAPHIC, "g-crew-names", "BRESNIK · PARMITANO (ESA) · DOUGLAS · RUBIO", "names only, no portraits (NASA likeness rule) unless the owner approves editorial use", 0.3),
    "p2-three": (GRAPHIC, "g-three", "3 SPACECRAFT · 3 ROCKETS", "three icons converge on one orbit; icons are original line art", 0.5),
    "p3-step1": (GRAPHIC, "g-step1", "STEP 1 · BLUE MOON TEST ARTICLE · UP TO 30 DAYS", "orbit diagram: lander dot enters circular orbit; 'ILLUSTRATION - NOT TO SCALE'", 0.3),
    "p3-step2": (GRAPHIC, "g-step2", "STEP 2 · ORION ON SLS · 18 × 1,122 MI → ~345 MI", "ellipse morphs to circle; numbers from NASA 2026-10-23", 0.3),
    "p3-step3": (PHOTO, "n5-solar", "STEP 3 · 2 DAYS OF CHECKOUT", "Orion hardware photo under the step label", 0.3),
    "p3-step4": (GRAPHIC, "g-step4", "STEP 4 · DOCK + ENTER · ~2 DAYS", "Orion docks to the port beside the lander's crew cabin; hatch-open icon; ILLUSTRATION", 0.4),
    "p3-step5": (GRAPHIC, "g-step5", "STEP 5 · STARSHIP · UP TO 2 HOURS · CREW STAYS IN ORION", "lower orbit line at 206 nmi; forward-port docking; ILLUSTRATION", 0.6),
    "p4-why": (GRAPHIC, "g-distance", "EARTH ORBIT: HOURS FROM HOME · NEAR THE MOON: DAYS", "contrast card; editorial framing, no numbers", 0.4),
    "p4-extra": (PHOTO, "n6-booster-rpsf", "UP TO 5 MORE DAYS · SPLASHDOWN: PACIFIC", "list builds over photo, dimmed", 0.3),
    "p5-2028": (PHOTO, "n2-orion", "ARTEMIS IV · FIRST LANDING · TARGET 2028", "push-out", 0.3),
    "p5-unknown": (GRAPHIC, "g-no-date", "LAUNCH: 2027 · DATE: NOT ANNOUNCED", "honest-unknown card", 0.4),
    "close": (PHOTO, "n1-boosters", "", "end on the booster tops, fade", 1.5),
}

# Per-line beats: scene -> one entry per voice line (kind, asset, on-screen text, direction). A new picture on
# every line keeps shots at ~2.5-8 s; long lines (> 8 s) get a camera move or a build inside the shot.
G, P = GRAPHIC, PHOTO
BEATS = {
    "h2-leo": [(G, "g-moon-x", "NOT THE MOON", "Moon outline (own line art) gets a strike; label NEXORA GRAPHIC"),
               (G, "g-feb-orbit", "FEB 27, 2026 · LOW EARTH ORBIT · 2027", "date stamp lands, then orbit ring draws around an Earth outline")],
    "h3-conops": [(P, "n4-conops", "NASA PLAN · OCT 23, 2026", "push-in on the NASA graphic; corner tag NASA CONCEPT GRAPHIC"),
                  (P, "n4-conops", "", "pan across the docking steps of the same NASA graphic")],
    "p1-feb": [(G, "g-timeline", "FEB 27, 2026", "timeline bar appears, Feb 27 marker"),
               (G, "g-timeline", "ARTEMIS III → EARTH ORBIT · 2027", "Artemis III marker slides to 'Earth orbit'"),
               (G, "g-timeline", "ARTEMIS IV → FIRST LANDING · 2028", "Artemis IV marker lands on the Moon icon")],
    "p1-why": [(P, "n2-orion", "", "Orion photo, slow push-in"),
               (G, "g-meet", "MEET · CONNECT · WORK TOGETHER", "two outline craft approach and lock (ILLUSTRATION)"),
               (P, "n2-orion", "", "Orion detail crop, push-out"),
               (G, "g-goals", "REDUCE RISK · VALIDATE HARDWARE · GAIN EXPERIENCE", "three words build; source NASA 2026-10-23")],
    "p1-quote": [(G, "g-quote", "\"keep testing like we fly\" - Amit Kshatriya, NASA", "quote card, source NASA 2026-02-27"),
                 (G, "g-quote2", "STANDARDIZE · RAISE FLIGHT RATE · SAFELY", "attribution: Jared Isaacman, NASA Administrator"),
                 (G, "g-yearly", "AFTER THE FIRST LANDING: ≥1 PER YEAR", "calendar ticks; 'stated plan'")],
    "p1-hardware": [(P, "n1-boosters", "", "booster tops, quick push"),
                    (P, "n3-rs25", "4 × RS-25 · JULY 2026", "engines photo"),
                    (P, "n2-orion", "ORION JOINED · JULY 2026", "Orion photo"),
                    (P, "n1-boosters", "NOSE CONES · SEP 30, 2026", "tilt to nose cones")],
    "p2-crew": [(G, "g-crew-names", "BRESNIK · PARMITANO (ESA) · DOUGLAS · RUBIO", "names one by one, roles beneath; no portraits"),
                (G, "g-14", "14 DAYS", "big number, source NASA 2026-10-23"),
                (G, "g-14", "PRACTICE: RENDEZVOUS · DOCKING · HABITATION", "list builds under 14 DAYS"),
                (G, "g-14", "PRACTICE: RENDEZVOUS · DOCKING · HABITATION · OPERATIONS", "list completes; hold")],
    "p2-three": [(G, "g-three", "NO APOLLO MISSION DID THIS", "title"),
                 (G, "g-three", "3 SPACECRAFT · 3 ROCKETS", "three outline icons rise from three pads and meet on one orbit")],
    "p3-step1": [(G, "g-step1", "STEP 1", "step card"),
                 (G, "g-step1", "BLUE MOON TEST ARTICLE → CIRCULAR LEO", "lander dot enters circular orbit; ILLUSTRATION - NOT TO SCALE"),
                 (G, "g-step1", "UP TO 30 DAYS", "counter ring")],
    "p3-step2": [(G, "g-step2", "STEP 2 · ORION ON SLS · KENNEDY", "Orion dot launches 'days later'"),
                 (G, "g-step2", "18 × 1,122 MILES", "ellipse draws with the two numbers"),
                 (P, "n5-solar", "~345 MILES · THERMAL STABILIZATION", "ellipse becomes a circle (inset) over the Orion solar-array photo")],
    "p3-step4": [(G, "g-step4", "STEP 4 · DOCK WITH BLUE MOON", "approach animation, ILLUSTRATION"),
                 (G, "g-step4", "HATCH OPEN", "hatch icon opens"),
                 (G, "g-step4", "~2 DAYS INSIDE", "day counter 1-2"),
                 (G, "g-step4", "PORT BESIDE THE CREW CABIN", "port highlighted on the outline"),
                 (G, "g-step4", "DOCKED TESTS · LIFE SUPPORT · COMMS · PROPULSION", "three checks tick (NASA 2026-02-27 plan)"),
                 (G, "g-step4", "FIRST CREWED EVALUATION OF A COMMERCIAL LUNAR LANDER", "undock animation")],
    "p3-step5": [(G, "g-step5", "STEP 5 · STARSHIP V3 TEST ARTICLE", "Starship outline launches from Florida"),
                 (G, "g-step5", "206 NAUTICAL MILES · COMMS COVERAGE", "lower orbit line under Orion's"),
                 (G, "g-step5", "ORION FORWARD PORT → STARSHIP NOSE", "forward-port docking, ILLUSTRATION"),
                 (G, "g-step5", "UP TO 2 HOURS", "timer"),
                 (G, "g-step5", "CREW STAYS IN ORION", "hatch closed icon")],
    "p4-why": [(G, "g-distance", "WHY?", "question card"),
               (G, "g-distance", "2 VEHICLES · 2 PROGRAMS · 1 LOCK", "two outlines lock"),
               (G, "g-distance", "EARTH ORBIT: HOURS FROM HOME", "left half lights"),
               (G, "g-distance", "NEAR THE MOON: DAYS", "right half lights; editorial framing, no numbers"),
               (P, "n2-orion", "THE SAFEST PLACE TO TRY IT FIRST", "Orion photo")],
    "p4-extra": [(P, "n5-solar", "UP TO 5 MORE DAYS", "photo, dimmed"),
                 (G, "g-extra", "SUITS · DOCKING SENSORS · ACOUSTIC & THERMAL · HUMAN FACTORS · SCIENCE & TECH", "list builds one item per ~2 s"),
                 (P, "n6-booster-rpsf", "SPLASHDOWN: PACIFIC · NASA + US NAVY", "photo, push-in")],
    "p5-2028": [(G, "g-2028", "IF THE DOCKINGS WORK", "card"),
                (P, "n2-orion", "ARTEMIS IV · FIRST LANDING · TARGET 2028", "Orion photo push-out"),
                (P, "n4-conops", "NASA · OCT 23, 2026", "NASA graphic again, wide")],
    "p5-unknown": [(G, "g-no-date", "LAUNCH: 2027 · DATE: NOT ANNOUNCED", "honest-unknown card"),
                   (G, "g-no-date", "THE ANSWER", "beat"),
                   (P, "n1-boosters", "NOT THE MOON - THE TEST BEFORE IT", "boosters, push-in, title echo")],
    "close": [(P, "n1-boosters", "", "tilt to the tops"), (P, "n1-boosters", "", "fade to black")],
}
CHAPTERS = {"p2-crew": "WHO FLIES", "p3-step1": "THE FLIGHT, STEP BY STEP", "p4-why": "WHY DOCK FIRST", "p5-2028": "WHAT IT MEANS"}
CHAPTER_S = 2.0


def build(lines):
    t, rows, prev, chap = 0.0, [], None, []
    seen = {}
    for ln in lines:
        sc = ln["scene"]
        if prev is not None and sc != prev:
            t += SHOTS[prev][4] + GAP_SCENE
            if sc in CHAPTERS:
                chap.append({"scene": "chapter:" + sc, "in": round(t - 0.35, 2), "out": round(t + CHAPTER_S - 0.35, 2),
                             "kind": GRAPHIC, "asset": "g-chapter", "on_screen": CHAPTERS[sc], "note": "chapter card, whoosh-free hard cut", "credit": "NEXORA graphic"})
                t += CHAPTER_S
        elif prev is not None:
            t += GAP_LINE
        j = seen.get(sc, 0); seen[sc] = j + 1
        rows.append({**ln, "beat": j, "start": round(t, 2), "end": round(t + ln["dur"], 2)})
        t += ln["dur"]; prev = sc
    total = round(t + SHOTS[prev][4] + 0.5, 2)
    shots = []
    for i, r in enumerate(rows):
        kind, asset, txt, note, _ = SHOTS[r["scene"]]
        b = BEATS.get(r["scene"])
        if b:
            kind, asset, txt, note = b[min(r["beat"], len(b) - 1)]
        start = 0.0 if i == 0 else round(r["start"] - 0.35, 2)
        shots.append({"scene": r["scene"], "beat": r["beat"], "in": start, "kind": kind, "asset": asset, "on_screen": txt,
                      "note": note, "credit": SLOTS[asset][0] if asset in SLOTS else "NEXORA graphic"})
    shots += [{**c, "beat": 0} for c in chap]
    shots.sort(key=lambda s: s["in"])
    for a, b in zip(shots, shots[1:]):
        a["out"] = b["in"]
    shots[-1]["out"] = total
    # chapter cards cut into the previous shot's tail; keep every shot positive
    shots = [s for s in shots if s["out"] - s["in"] > 0.05]
    return rows, shots, total


def claims_by_scene():
    s = re.sub(r"<!--.*?-->", "", open(os.path.join(HERE, "script.md"), encoding="utf-8").read(), flags=re.S)
    cur, out = None, {}
    for l in s.splitlines():
        if l.startswith("[SCENE:"):
            cur = l[7:-1].strip(); continue
        if cur:
            out.setdefault(cur, set()).update(re.findall(r"\[\[([^\]]+)\]\]", l))
    return {k: sorted(v) for k, v in out.items()}


def srt_time(x):
    h, r = divmod(x, 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


def captions(rows):
    cues = []
    for r in rows:
        words = r["text"].split()
        chunks, cur = [], []
        for w in words:                      # phrase cues of <= 7 words / 42 chars
            if cur and (len(cur) >= 7 or len(" ".join(cur + [w])) > 42):
                chunks.append(cur); cur = []
            cur.append(w)
        if cur: chunks.append(cur)
        n = sum(len(" ".join(c)) for c in chunks)
        t = r["start"]
        for c in chunks:
            d = r["dur"] * len(" ".join(c)) / n
            cues.append((t, t + d, " ".join(c))); t += d
    return "\n".join(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{txt}\n" for i, (a, b, txt) in enumerate(cues, 1))


def scenes_json(shots, claims):
    out = []
    for s in shots:
        d = round(s["out"] - s["in"], 2)
        base = {"id": f"{s['scene'].replace(':', '-')}-{s['beat']}", "duration": d, "claim_ids": claims.get(s["scene"].split(":")[-1] if not s["scene"].startswith("chapter") else "", []), "note": s["note"][:200]}
        if s["kind"] == PHOTO:
            out.append({**base, "type": "photo", "src": f"assets/{s['asset']}.jpg", "credit": SLOTS[s["asset"]][0],
                        "license": "PD-US-Gov", "camera": {"from": [0.5, 0.62, 1.0], "to": [0.5, 0.45, 1.10]}})
        else:
            words = s["on_screen"].replace("·", " ").split()
            out.append({**base, "type": "kinetic", "text": " ".join(words[:18]), "emphasis": words[:1]})
    return {"version": 1, "output": {"width": 1920, "height": 1080, "fps": 30}, "scenes": out,
            "_note": "photo scenes need the NASA originals in assets/ (ASSETS_NEEDED.md); graphic scenes are placeholders as kinetic "
                     "cards until the animated graphics in graphics/ are rendered"}


def main():
    lines = json.load(open(os.path.join(HERE, "voice_temp", "lines.json")))
    missing = [l["scene"] for l in lines if l["scene"] not in SHOTS]
    if missing:
        print(json.dumps({"result": "ERROR", "error": f"scenes without a shot: {sorted(set(missing))}"})); return 2
    rows, shots, total = build(lines)
    claims = claims_by_scene()
    with open(os.path.join(HERE, "edit_plan_shots.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["#", "in_s", "out_s", "dur_s", "scene", "kind", "asset_or_graphic", "credit_on_screen", "on_screen_text", "direction", "claims"])
        for i, s in enumerate(shots, 1):
            w.writerow([i, s["in"], s["out"], round(s["out"] - s["in"], 2), s["scene"], s["kind"], s["asset"], s["credit"], s["on_screen"], s["note"], " ".join(claims.get(s["scene"].split(":")[-1] if not s["scene"].startswith("chapter") else "", []))])
    with open(os.path.join(HERE, "edit_plan.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["second", "timecode", "scene", "visual", "asset_or_graphic", "on_screen_text", "voice (temp)"])
        for sec in range(int(total) + 1):
            sh = next((s for s in shots if s["in"] <= sec + 0.5 < s["out"]), shots[-1])
            vo = " / ".join(r["text"] for r in rows if r["start"] < sec + 1 and r["end"] > sec)
            w.writerow([sec, f"{sec // 60}:{sec % 60:02d}", sh["scene"], sh["kind"], sh["asset"], sh["on_screen"], vo])
    open(os.path.join(HERE, "captions_temp.srt"), "w").write(captions(rows))
    json.dump(scenes_json(shots, claims), open(os.path.join(HERE, "scenes.json"), "w"), indent=1, ensure_ascii=False)
    hook = [s for s in shots if s["in"] < 20]
    summary = {"total_s": total, "total_min": round(total / 60, 2), "voice_s": round(sum(l["dur"] for l in lines), 1),
               "shots": len(shots), "photo_share": round(sum(s["out"] - s["in"] for s in shots if s["kind"] == PHOTO) / total, 2),
               "slots_used": {k: [s["scene"] for s in shots if s["asset"] == k] for k in SLOTS},
               "hook_first_20s": [{k: s[k] for k in ("scene", "in", "out", "kind", "asset")} for s in hook],
               "subject_on_screen_at": next(s["in"] for s in shots if s["asset"] == "n1-boosters")}
    json.dump(summary, open(os.path.join(HERE, "timeline_summary.json"), "w"), indent=1)
    print(json.dumps({"result": "ok", **{k: summary[k] for k in ("total_s", "total_min", "shots", "photo_share", "subject_on_screen_at")}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
