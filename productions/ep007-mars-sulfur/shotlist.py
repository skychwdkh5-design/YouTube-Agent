"""Write script + shot list with real timecodes and the source of every frame."""
import importlib, json, sys
SRCDESC = {"PIA26309": "PIA26309 Mastcam, crystals in crushed rock, June 7 2024", "PIA26307": "PIA26307 MAHLI close-up, Convict Lake, June 4 2024",
 "PIA26308": "PIA26308 MAHLI, Snow Lake stone, June 8 2024", "PIA26245": "PIA26245 HiRISE, rover from orbit, Dec 29 2023",
 "PIA26363": "PIA26363 Mastcam 360°, sol 4,220, June 19 2024 (lossless PNG)", "PIA26410": "PIA26410 Mastcam pano, Sept 21-22 2024",
 "PIA26366": "PIA26366 Mastcam, rocks with halos, May 7 2024", "PIA26210": "PIA26210 Mastcam, last look at sulfur field, Oct 11 2024",
 "PIA26367": "PIA26367 Mastcam, Gediz Vallis, Mar 31 2024", "PIA26471": "PIA26471 Mastcam 360°, sol 4,352, Nov 2 2024"}
def tc(x): return f"{int(x//60)}:{x%60:04.1f}"
out = []
for mod, vdir, title in [("beats", "voice", "EP007 long-form (draft)"), ("short1", "voice_short1", "Short 1 — The rock Curiosity broke"), ("short2", "voice_short2", "Short 2 — Invisible from orbit")]:
    B = importlib.import_module(mod).BEATS; t = json.load(open(f"{vdir}/narration.timing.json"))
    starts = [0.0] + [b["start"] - 0.12 for b in t["beats"][1:]] + [t["duration"]]
    out.append(f"\n## {title} — {tc(t['duration'])}\n\n| Time | Narration | On screen | Source |\n|---|---|---|---|")
    for i, (text, shots) in enumerate(B):
        b0, b1 = starts[i], starts[i + 1]
        for j, (kind, ref, o) in enumerate(shots):
            s = b0 + (b1 - b0) * j / len(shots)
            what = (o.get("label") or "").title() or ("Graphic " + ref + (f" step {o['step']}" if o.get("step") else "") if "graphic" in kind else "Real image, Ken Burns")
            src = SRCDESC.get(ref, "Original graphic (OrbitalAtlas); facts per research.md")
            out.append(f"| {tc(s)} | {text if j == 0 else '…'} | {what} | {src} |")
open("script_and_shotlist.md", "w").write("# EP007 — Pure sulfur on Mars: script and shot list\n\nDraft voice: Kokoro am_michael (temporary, free). Final voice: Adam (ElevenLabs) after approval.\nImages: NASA/JPL-Caltech/MSSS; HiRISE: NASA/JPL-Caltech/University of Arizona. No music. No reconstruction of the crushing (none exists on video).\n" + "\n".join(out) + "\n")
print("ok")
