"""EP012 timing: the real Adam narration, with short pauses added only at the TTS chunk joins.
Words are never stretched or cut; V(t) maps a narration time to the film time."""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
VOICE = os.path.join(ROOT, "voice", "narration.wav")
VJ = json.load(open(os.path.join(ROOT, "voice", "narration.voice.json")))
WORDS = VJ["words"]
NDUR = VJ["duration"]

# v2 order: the finished sentence "The sampler's arm kept sinking ... pull the spacecraft away." opens the film,
# then the hook runs from "This is a real camera" as recorded. Cuts sit in recorded silences only.
# SEGMENTS = (narration start, narration end, silence inserted before it). No word is stretched or cut.
SEGMENTS = [(19.93, 27.95, 0.25), (0.0, 19.93, 0.55), (27.95, 167.23, 0.0), (167.23, 333.949, 0.70),
            (333.949, NDUR, 0.60)]
TAIL = 5.0  # end card after the last word

_starts = []
_f = 0.0
for _a, _b, _g in SEGMENTS:
    _f += _g
    _starts.append(_f)
    _f += _b - _a
VOICE_END = _f


def V(t):
    """narration time -> film time."""
    for (a, b, g), f0 in zip(SEGMENTS, _starts):
        if a - 1e-6 <= t < b - 1e-9 or (b == NDUR and abs(t - b) < 1e-6):
            return f0 + (t - a)
    raise ValueError(t)


END = round((VOICE_END + TAIL) * 30) / 30


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
