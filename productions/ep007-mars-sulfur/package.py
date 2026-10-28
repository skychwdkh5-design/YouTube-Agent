"""EP007 publish texts. Chapters are computed from the FINAL narration timing (beat starts), never typed by hand.
python3 package.py <voice_dir_long> <long_mp4_seconds>  -> package/description_long.txt, shorts texts"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
vdir = sys.argv[1]
tim = json.load(open(os.path.join(HERE, vdir, "narration.timing.json")))
runtime = float(sys.argv[2])
CH = [(0, "Yellow crystals on Mars"), (5, "The accident"), (14, "How they knew it was sulfur"),
      (19, "Why it shouldn't be there"), (25, "A whole field, invisible from orbit"), (31, "Gediz Vallis channel"),
      (34, "Drill hole #41 at Mammoth Lakes"), (40, "What scientists think now"), (49, "Not evidence of life"),
      (53, "Where it stands")]


def tc(s):
    s = int(s); return f"{s // 60}:{s % 60:02d}"


starts = [0.0] + [b["start"] for b in tim["beats"][1:]]
chapters = "\n".join(f"{tc(starts[i] if i else 0)} {name}" for i, name in CH)
rt = f"{int(runtime // 60)}:{int(runtime % 60):02d}"
TITLE = "NASA’s Rover Ran Over a Rock on Mars. This Was Inside."
long_desc = f"""{TITLE}

In May 2024, NASA's Curiosity rover drove over a rock in Gediz Vallis channel on Mount Sharp, Mars, and cracked it open. Inside were yellow crystals. The rover's APXS instrument identified them as elemental sulfur, the first pure sulfur ever found on Mars. NASA's project scientist: "It shouldn't be there, so now we have to explain it."

We follow the find with NASA's own images: how the team knew it was sulfur, why it was a surprise, why the stones were invisible from orbit, and what scientists think now.

CHAPTERS
{chapters}

WHAT IS CONFIRMED, AND WHAT IS NOT
- Confirmed (NASA/JPL): pure elemental sulfur, a whole field of sulfur stones, too brittle to drill; no evidence of volcanoes or hot springs near this part of Mount Sharp.
- Peer reviewed (Science, 2026): the stones appear to have formed in place, roughly 3 billion years ago; the authors PROPOSE magmatic vapor as the source.
- Not peer reviewed (conference abstracts, 2026): an impact-melt idea that depends on a rock layer nobody has measured yet.
- Not claimed: evidence of life. There is no video of the moment the rock cracked; only photos taken afterwards.

SOURCES
- NASA/JPL, "NASA's Curiosity Rover Discovers a Surprise in a Martian Rock" (July 18, 2024): https://www.jpl.nasa.gov/news/nasas-curiosity-rover-discovers-a-surprise-in-a-martian-rock/
- NASA/JPL, "NASA's Curiosity Mars Rover Takes a Last Look at Mysterious Sulfur" (Nov. 18, 2024): https://www.jpl.nasa.gov/news/nasas-curiosity-mars-rover-takes-a-last-look-at-mysterious-sulfur/
- VanBommel et al., "A native sulfur deposit in Gale crater, Mars," Science 393, 820-825 (2026), doi:10.1126/science.adu5501: https://www.science.org/doi/10.1126/science.adu5501
- Washington University in St. Louis release on the Science paper: https://artsci.washu.edu/node/28889
- Rapin et al., EGU26-22162: https://meetingorganizer.copernicus.org/EGU26/EGU26-22162.html
- Maggioni et al., EGU26-12327: https://meetingorganizer.copernicus.org/EGU26/EGU26-12327.html

IMAGES
NASA/JPL-Caltech/MSSS: PIA26307, PIA26308, PIA26309, PIA26210, PIA26363, PIA26366, PIA26367, PIA26410, PIA26471 (Mastcam, MAHLI).
NASA/JPL-Caltech/University of Arizona: PIA26245 (HiRISE, enhanced color).
Diagrams are OrbitalAtlas schematics, not to scale. Use of NASA imagery does not imply NASA endorsement.

Narration: ElevenLabs synthetic voice (Adam). Runtime {rt}.
Made by OrbitalAtlas.
"""
SH = {
 "short1": ("Curiosity Ran Over a Rock on Mars. Pure Sulfur Was Inside.",
            "NASA's Curiosity rover cracked a rock in Gediz Vallis, Mars, in 2024. Inside: yellow crystals of pure sulfur, the first ever found on Mars. How they formed is still debated.\n\nImages: NASA/JPL-Caltech/MSSS (Mastcam, MAHLI).\n#Shorts #Mars #space #NASA"),
 "short2": ("Mars From Orbit: Nothing. On the Ground: Pure Sulfur",
            "From orbit, this patch of Mars looked unremarkable: the HiRISE camera can see Curiosity, but not the stones. On the ground, the rover found a field of them, made of pure sulfur.\n\nImages: NASA/JPL-Caltech/University of Arizona (HiRISE); NASA/JPL-Caltech/MSSS (Mastcam, MAHLI).\n#Shorts #Mars #space #NASA"),
}
os.makedirs(os.path.join(HERE, "package"), exist_ok=True)
open(os.path.join(HERE, "package", "description_long.txt"), "w").write(long_desc)
json.dump({k: {"title": t, "description": d} for k, (t, d) in SH.items()} | {"long": {"title": TITLE}},
          open(os.path.join(HERE, "package", "texts.json"), "w"), indent=1, ensure_ascii=False)
print(chapters); print(len(long_desc), "chars")
