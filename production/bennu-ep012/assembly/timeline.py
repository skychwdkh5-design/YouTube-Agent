"""EP012 timing: the real Adam narration, with short pauses added only at the TTS chunk joins.
Words are never stretched or cut; V(t) maps a narration time to the film time."""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
VOICE = os.path.join(ROOT, "voice", "narration.wav")
VJ = json.load(open(os.path.join(ROOT, "voice", "narration.voice.json")))
WORDS = VJ["words"]
NDUR = VJ["duration"]

# (narration time, silence inserted before it). 0.25 s lead-in, then the two chunk joins.
GAPS = [(0.0, 0.25), (167.23, 0.70), (333.949, 0.60)]
TAIL = 5.0  # end card after the last word


def V(t):
    return t + sum(g for at, g in GAPS if t >= at - 1e-6)


END = round((V(NDUR) + TAIL) * 30) / 30


def _norm(s):
    return re.sub(r"[^a-z0-9.]", "", s.lower()).rstrip(".")


def word(phrase, after=0.0):
    """narration start time of the first occurrence of `phrase` (word sequence) at/after `after`."""
    p = [_norm(x) for x in phrase.split()]
    for i in range(len(WORDS) - len(p) + 1):
        if WORDS[i]["start"] + 1e-6 < after:
            continue
        if all(_norm(WORDS[i + k]["text"]) == p[k] for k in range(len(p))):
            return WORDS[i]["start"]
    raise KeyError(phrase)
