"""EP008 Artemis III - single source of truth for script + edit map.

python3 beats.py   -> script/SCRIPT.md, script/EDIT_MAP.md, script/edit_map.json, script/narration.txt

Timing is ESTIMATED (no voice yet): words / WPM. After the approved voice exists, shot times are
re-derived from narration timing (same as EP007). Every scene lists the fact ids (research/RESEARCH.md)
it states; QC checks that each id exists and that no shot holds longer than MAX_HOLD seconds.
"""
import json, re, pathlib

WPM = 150            # Adam pace on EP007 was ~148 wpm
MAX_HOLD = 6.0       # no single photo framing longer than this (retention playbook: no long static scenes)
MAX_DIAGRAM = 9.0    # animated diagram beat; must visibly change within the beat
HERE = pathlib.Path(__file__).parent

# shot = (asset_id, share_of_scene, motion, on_screen_text, label)
# label is the honesty label shown on screen for illustrations/graphics.
S = []
def scene(sid, title, facts, vo, shots, sfx=""):
    S.append(dict(id=sid, title=title, facts=facts, vo=" ".join(vo.split()), shots=shots, sfx=sfx))

# ---------------------------------------------------------------- 0:00 cold open
scene("s01", "Cold open: the plan vs the new plan", ["F04", "F02", "F06"],
 "NASA's next Moon mission was supposed to land here. Now it won't even leave Earth orbit.",
 [("a2-lunar-surface", .45, "fast push-in 104->110%", "THE PLAN: LAND HERE", "NASA · ARTEMIS II PHOTO, APR 2026"),
  ("d-orbit-vs-moon", .55, "hard cut, zoom out from Moon to Earth, LEO ring lights up", "NOW: 273 MILES UP", "DIAGRAM")],
 sfx="0.0 low sub hit; 1.3 whoosh-reverse into cut; 1.4 impact + silence 0.2 s")

scene("s02", "The surprising fact", ["F03", "F14", "F20"],
 "In April, four astronauts flew around the Moon on Artemis Two. And the next crew's rocket won't even carry the stage that sends Orion toward the Moon. "
 "In its place: a metal barrel with no engine.",
 [("a2-earthset", .27, "slow drift L->R", "ARTEMIS II · APRIL 2026", "NASA · ARTEMIS II PHOTO"),
  ("d-sls-stack", .38, "upper stage slides out, spacer slides in", "UPPER STAGE → SPACER", "DIAGRAM · NASA HARDWARE UPDATE"),
  ("spacer", .35, "push-in on barrel", "NO ENGINE", "NASA/SAM LOTT")],
 sfx="tick on each on-screen word; metallic clank on 'barrel'")

scene("s03", "Why it matters + promise", ["F01", "F02", "F06", "F13"],
 "NASA made this change back in February, and in October it published the full plan: fourteen days in orbit, "
 "two Moon landers, and one test that has to work before anyone lands near the lunar South Pole. "
 "Here's what they'll actually do up there, and why NASA decided the Moon can wait a year.",
 [("d-timeline", .40, "playhead runs Feb 27 → Oct 23", "ANNOUNCED FEB 27, 2026", None),
  ("conops-graphic", .35, "pan across, highlight two docking points", "14 DAYS · 2 LANDERS", "NASA CONCEPT GRAPHIC"),
  ("a2-hertzsprung", .25, "slow push to South Pole direction", "LANDING: 2028", "NASA · ARTEMIS II PHOTO")],
 sfx="music bed enters at 'Here's what' (low, pulsing)")

# ---------------------------------------------------------------- 0:30 what changed
scene("s04", "What NASA changed in February", ["F03", "F04", "F01", "F02", "S1"],
 "Artemis Two's flight took ten days: launch on April first, a seven-hour lunar flyby on April sixth, splashdown off California on April tenth. "
 "But by then the plan for the next mission had already changed. On February twenty-seventh, NASA rewrote the order of the Artemis program. Artemis Three had been the landing. "
 "It became a test flight in low Earth orbit, set for twenty twenty-seven, and the first landing moved to Artemis Four, targeted for twenty twenty-eight. "
 "NASA also promised at least one landing every year after that. "
 "At the announcement, NASA's leadership argued that rare flights are a problem in themselves: crews and launch teams lose practice between missions, "
 "and changing the rocket and spacecraft after every flight adds risk instead of removing it.",
 [("a2-earth-behind-moon", .12, "slow drift", "ARTEMIS II · APR 1-10, 2026", "NASA · ARTEMIS II PHOTO"),
  ("a2-earthset", .10, "push-in on Earth", "APRIL 6: FLYBY", "NASA · ARTEMIS II PHOTO"),
  ("cadence-infographic", .14, "push-in on 2027 slot", "FEB 27, 2026", "NASA GRAPHIC"),
  ("d-timeline", .16, "Artemis III block slides from 'LANDING' to 'EARTH ORBIT'", "ARTEMIS III → TEST FLIGHT", None),
  ("d-timeline", .16, "Artemis IV highlighted", "FIRST LANDING: ARTEMIS IV · 2028", None),
  ("rs25", .32, "slow pan across four engines", "SAME ROCKET, MORE OFTEN", "NASA/BEN SMEGELSKY")],
 sfx="soft paper/whoosh on each timeline move")

# ---------------------------------------------------------------- 1:20 the hardware is real
scene("s05", "The hardware already exists", ["F15", "F16", "F18", "F17", "F14", "F22"],
 "And this isn't a paper mission. The four main engines for Artemis Three reached Kennedy Space Center in July. "
 "The Orion capsule and its service module were joined in late July. "
 "On September thirtieth, technicians put the nose cones on the twin boosters, finishing the stack. "
 "More than two hundred and fifty parts from Artemis Two's Orion are being reused on later missions, and NASA says reused parts move some installation work up by about three months. "
 "Even the launch tower is being turned around for its next flight nearly fifty percent faster. "
 "And that missing upper stage? It isn't scrapped. NASA reassigned it to Artemis Four, the mission that actually has to reach the Moon.",
 [("rs25", .16, "tilt up", "JULY 2026", "NASA/BEN SMEGELSKY"),
  ("orion-joined", .23, "slow vertical pan (portrait in 16:9 with blurred fill)", "ORION · ARTEMIS III", "NASA/AMANDA STEVENSON"),
  ("srb-nosecones", .23, "vertical tilt down the booster", "SEPT 30: BOOSTERS STACKED", "NASA/CORY S HUSTON"),
  ("solar-array", .14, "push-in", "250+ ARTEMIS II PARTS REUSED", "NASA/AMANDA STEVENSON"),
  ("d-timeline", .10, "'~3 MONTHS' and '~50% FASTER' counters", "FASTER TURNAROUND", None),
  ("d-sls-stack", .14, "upper stage moves from A-III stack to A-IV stack", "UPPER STAGE → ARTEMIS IV", "DIAGRAM")],
 sfx="room tone of a high bay (library SFX), light mechanical clicks")

scene("s06", "Who flies", ["F05", "F23"],
 "The crew is Randy Bresnik, Andre Douglas and Frank Rubio of NASA, and Luca Parmitano of the European Space Agency. "
 "In September they trained with Navy helicopter crews off San Diego, practicing being hoisted out of the water after splashdown. "
 "They've drilled escaping a capsule underwater, trained in their orange survival suits, and tasted nearly two hundred items of space food. "
 "Their mission will be about two weeks long, and it will never get farther than a few hundred miles from home.",
 [("d-crew-names", .30, "names type on over Earth limb graphic, no portraits", "THE CREW", "NAMES ONLY"),
  ("d-training-list", .40, "4 training items tick in, icons only, no crew photos", "TRAINING · SEPT 2026", "GRAPHIC · NASA STATUS 2026-10-13"),
  ("d-orbit-vs-moon", .30, "Moon distance bar vs LEO ring", "~345 MI vs ~239,000 MI", "DIAGRAM")],
 sfx="")

# ---------------------------------------------------------------- 2:05 the mission
scene("s07", "Three launches", ["F11", "F09"],
 "Artemis Three needs three launches. First, Blue Origin launches a test version of its Blue Moon lander. "
 "It can wait in orbit for up to thirty days. "
 "Then the crew launches on NASA's SLS rocket from Florida. Starship goes up after the crew is already in orbit.",
 [("d-mission-sequence", .35, "launch 1 arc, Blue Moon icon parks in orbit, 30-day counter", "LAUNCH 1: BLUE MOON", "ILLUSTRATION"),
  ("d-mission-sequence", .35, "launch 2 from Florida, Orion icon", "LAUNCH 2: CREW", "ILLUSTRATION"),
  ("d-mission-sequence", .30, "launch 3, Starship icon", "LAUNCH 3: STARSHIP", "ILLUSTRATION")],
 sfx="three distinct launch rumbles, each shorter")

scene("s08", "The orbits", ["F06"],
 "The orbits are precise. The Blue Moon test article circles about two hundred seventy-three miles up. "
 "Orion starts in a long, stretched orbit, from eighteen to more than eleven hundred miles, then rounds it out near three hundred forty-five. "
 "Starship flies lower still. Every number here comes from NASA's flight profile.",
 [("conops-graphic", .40, "zoom to orbit annotations", "273 MI · 345 MI", "NASA CONCEPT GRAPHIC"),
  ("d-orbit-vs-moon", .60, "ellipse 18 x 1,122 mi animates, circularizes", "18 × 1,122 MI → 345 MI", "DIAGRAM · NASA FIGURES")],
 sfx="soft UI ticks on numbers")

scene("s09", "Dock one: Blue Moon", ["F07", "F08", "F09"],
 "First docking: Orion pulls up alongside the Blue Moon lander. While they're joined, Orion's own software flies both spacecraft. "
 "Then the hatch opens. Up to two astronauts, in their orange survival suits, float into a lunar lander for the first time since Apollo. "
 "They spend about two days checking its cabin, controls and life support. "
 "Riding along is a dummy the weight of a spacesuit, wired with sensors, reporting what the cabin really feels like.",
 [("d-mission-sequence", .30, "Orion approaches, side-by-side dock, 'ORION SOFTWARE IN CONTROL'", "DOCK 1: BLUE MOON", "ILLUSTRATION - NOT REAL FOOTAGE"),
  ("d-mission-sequence", .25, "hatch icon opens, 2 figures move across", "UP TO 2 ASTRONAUTS INSIDE", "ILLUSTRATION"),
  ("d-mission-sequence", .25, "48-hour clock runs", "~2 DAYS", "ILLUSTRATION"),
  ("a2-orion-sunlit", .20, "slow push", "ORION", "NASA · ARTEMIS II PHOTO")],
 sfx="docking latch clunk (library), hatch hiss")

scene("s10", "Dock two: Starship", ["F10", "F19"],
 "Second docking: Starship. The test vehicle is a hundred seventy-one feet tall, about fifty-two meters, with a docking port in its nose. "
 "Orion meets it nose to nose, and this time SpaceX flies the pair. It lasts up to two hours, and nobody goes inside. "
 "NASA and SpaceX are still deciding exactly which control and communication tests to run.",
 [("d-mission-sequence", .35, "Starship icon at true scale next to Orion (171 ft)", "171 FT · 52 M", "ILLUSTRATION"),
  ("d-mission-sequence", .35, "nose-to-nose dock, 2:00:00 countdown", "UP TO 2 HOURS", "ILLUSTRATION - NOT REAL FOOTAGE"),
  ("d-mission-sequence", .30, "crew icon stays in Orion, red X on Starship hatch", "CREW STAYS IN ORION", "ILLUSTRATION")],
 sfx="lower, heavier clunk; countdown ticks")

scene("s11", "Home", ["F12", "F06"],
 "After about fourteen days, Orion comes home and splashes down in the Pacific, off the coast of California, "
 "the same ocean where Artemis Two landed in April.",
 [("d-mission-sequence", .45, "reentry arc to Pacific", "SPLASHDOWN: PACIFIC", "ILLUSTRATION"),
  ("a2-earth-behind-moon", .55, "slow drift", "DAY 14", "NASA · ARTEMIS II PHOTO")],
 sfx="wind/water swell")

# ---------------------------------------------------------------- 4:40 why docking first
scene("s12", "Why docking first", ["F02", "F13", "F08", "F10"],
 "So why test this in Earth orbit? Because on Artemis Four, the landing depends on exactly this step. "
 "Orion can't land. A commercial lander has to meet it, take astronauts down near the South Pole, and bring them back. "
 "If that handoff fails near the Moon, the crew is days from home. In low Earth orbit, they're hours away.",
 [("d-orbit-vs-moon", .35, "Artemis IV path draws out to Moon, handoff point flashes", "ARTEMIS IV: HANDOFF AT THE MOON", "DIAGRAM"),
  ("a2-tiny-earth", .30, "slow push", "DAYS FROM HOME", "NASA · ARTEMIS II PHOTO"),
  ("d-orbit-vs-moon", .35, "snap back to LEO ring", "HOURS FROM HOME", "DIAGRAM")],
 sfx="tension drone builds; cut to silence on 'hours away'")
# NOTE s12: 'days from home / hours away' is a general orbital-mechanics statement, not a NASA-stated reason.
# The VO frames it as why the test is placed in LEO in principle; NASA's stated purpose (F08/F10, July 15)
# is to test rendezvous and docking between commercial landers and Orion. Owner to confirm wording.

scene("s13", "Apollo did this too", ["F21"],
 "If this sounds familiar, it should. In March nineteen sixty-nine, Apollo Nine tested the lunar module in Earth orbit. "
 "Four months later, Apollo Eleven landed.",
 [("d-timeline-apollo", .55, "1969 timeline: Apollo 9 (Earth orbit) → Apollo 11 (landing)", "APOLLO 9 · EARTH ORBIT · 1969", "DIAGRAM"),
  ("a2-earthrise", .45, "slow push", "ARTEMIS: 2027 → 2028", "NASA · ARTEMIS II PHOTO")],
 sfx="")
# Apollo 9: launched 1969-03-03; Apollo 11 landed 1969-07-20 (about 4.5 months). Historical parallel only.

# ---------------------------------------------------------------- 5:40 unknowns + close
scene("s14", "What is still unknown", ["S2", "F18", "F19"],
 "What we don't know yet: a launch date. NASA says twenty twenty-seven; its administrator told reporters in October that next summer is still the target. "
 "The rocket's fueling test at the pad is still ahead. And NASA hasn't said which lander will carry the first crew down on Artemis Four.",
 [("srb-nosecones", .40, "tilt", "LAUNCH: 2027 (NO DATE)", "NASA/CORY S HUSTON"),
  ("d-timeline", .30, "open items flash: tanking test, lander choice", "STILL OPEN", None),
  ("a2-earthset", .30, "drift", "ARTEMIS IV: WHICH LANDER?", "NASA · ARTEMIS II PHOTO")],
 sfx="")

scene("s15", "Close", ["F02", "F13"],
 "So the next Moon mission stays close to home, on purpose. If both dockings work, the following crew goes all the way down. "
 "Artemis Four is the landing. Artemis Three is the test it can't skip.",
 [("d-orbit-vs-moon", .40, "LEO ring → path to Moon", "ARTEMIS III: THE TEST", "DIAGRAM"),
  ("a2-lunar-surface", .60, "slow push - bookends frame 1", "ARTEMIS IV: THE LANDING", "NASA · ARTEMIS II PHOTO")],
 sfx="music resolves; 1 s tail; end screen 10 s (silent, not counted)")


def words(t):
    return len(re.findall(r"[A-Za-z0-9'’-]+", t))


def build():
    out = HERE / "script"; out.mkdir(exist_ok=True)
    t = 0.0; rows = []; problems = []
    known = set(re.findall(r"\| (F\d\d|S\d) \|", (HERE / "research/RESEARCH.md").read_text()))
    for s in S:
        dur = words(s["vo"]) / WPM * 60 + 0.4
        s["start"], s["dur"] = round(t, 1), round(dur, 1)
        for f in s["facts"]:
            if f not in known:
                problems.append(f"{s['id']}: fact {f} not in RESEARCH.md")
        tot = sum(sh[1] for sh in s["shots"])
        if abs(tot - 1) > 0.01:
            problems.append(f"{s['id']}: shot shares sum to {tot}")
        st = t
        for i, (aid, share, motion, txt, label) in enumerate(s["shots"], 1):
            d = dur * share
            # Composition reset rule: a photo never holds one framing longer than MAX_HOLD; an animated
            # diagram (d-*) keeps changing on screen, so it may run to MAX_DIAGRAM split into beats.
            limit = MAX_DIAGRAM if aid.startswith("d-") else MAX_HOLD
            n = max(1, -(-int(d * 10) // int(limit * 10)))
            for k in range(n):
                part = d / n
                if n == 1:
                    sid, mo = f"{s['id']}.{i}", motion
                elif aid.startswith("d-"):
                    sid, mo = f"{s['id']}.{i}{'abcdef'[k]}", f"{motion} - beat {k+1}/{n}"
                else:
                    sid, mo = f"{s['id']}.{i}{'abcdef'[k]}", (motion if k == 0 else f"re-frame: {['detail crop 1.4x', 'opposite-side crop', 'wide pull-back'][(k-1) % 3]}")
                rows.append(dict(scene=s["id"], shot=sid, start=round(st, 1), end=round(st + part, 1),
                                 asset=aid, motion=mo, on_screen=txt if k == 0 else "", label=label))
                st += part
        t += dur
    return rows, t, problems


if __name__ == "__main__":
    rows, total, problems = build()
    out = HERE / "script"
    wc = sum(words(s["vo"]) for s in S)
    md = [f"# EP008 script — NASA Changed Its Moon Mission. Here's Why.\n",
          f"Draft for owner review. {wc} words, estimated {total/60:.0f}:{total%60:02.0f} at {WPM} wpm (timing re-derived after voice).",
          "Fact ids → `research/RESEARCH.md`. Numbers spelled out for TTS. No voice generated.\n"]
    for s in S:
        md += [f"## {s['id']} · {int(s['start']//60)}:{int(s['start']%60):02d} · {s['title']}",
               f"*Facts: {', '.join(s['facts'])}*\n", s["vo"] + "\n"]
    (out / "SCRIPT.md").write_text("\n".join(md))
    (out / "narration.txt").write_text("\n\n".join(s["vo"] for s in S) + "\n")
    em = ["# EP008 edit map (estimated seconds)\n",
          "| shot | start | end | asset | motion | on screen | credit/label |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        em.append(f"| {r['shot']} | {r['start']:.1f} | {r['end']:.1f} | {r['asset']} | {r['motion']} | {r['on_screen']} | {r['label'] or ''} |")
    em += ["", "## Sound per scene", ""] + [f"- **{s['id']}**: {s['sfx'] or 'music bed only'}" for s in S]
    em += ["", "## Checks", "", "- " + ("PASS: every fact id exists; photo framings <= %.0f s, diagram beats <= %.0f s" % (MAX_HOLD, MAX_DIAGRAM) if not problems else "\n- ".join(problems))]
    (out / "EDIT_MAP.md").write_text("\n".join(em) + "\n")
    json.dump({"wpm": WPM, "total_s": round(total, 1), "words": wc, "scenes": S, "shots": rows, "problems": problems},
              open(out / "edit_map.json", "w"), indent=1)
    print(f"{wc} words, {total:.0f}s, {len(rows)} shots, problems: {len(problems)}")
    for p in problems: print(" -", p)
