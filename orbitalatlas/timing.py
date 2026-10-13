"""Animation timing: scalar tracks and narration-timed cues.

Narration sync is only as good as the timing source: `Cues.from_words` takes PROVIDER word timestamps
(e.g. ElevenLabs with-timestamps). Estimated timing must be marked `source='estimated'` and is never reported as frame-accurate."""
import re
from . import easing as E


class Track:
    """scalar animation channel: keys [(t, value)], per-segment easing, hold before/after."""
    def __init__(self, keys, ease="smoother"):
        self.keys = sorted(keys); self.ease = E.get(ease)
    def __call__(self, t):
        k = self.keys
        if t <= k[0][0]: return k[0][1]
        if t >= k[-1][0]: return k[-1][1]
        for (t0, v0), (t1, v1) in zip(k, k[1:]):
            if t0 <= t <= t1: return E.lerp(v0, v1, self.ease(E.seg(t, t0, t1)))


def stagger(n, start, step):
    return [start + i * step for i in range(n)]


class Cues:
    """named times looked up from word timestamps. words: [{'text','start','end'}] in seconds."""
    def __init__(self, words, offset=0.0, source="provider"):
        assert source in ("provider", "estimated")
        self.source = source; self.offset = offset
        self.words = [dict(text=w["text"], start=w["start"] - offset, end=w["end"] - offset) for w in words]
        self._norm = [re.sub(r"[^\w']", "", w["text"].lower()) for w in self.words]

    @classmethod
    def from_words(cls, words, offset=0.0, source="provider"): return cls(words, offset, source)

    def find(self, phrase, occurrence=1):
        """index of the first word of the n-th occurrence of `phrase` (case/punctuation-insensitive)."""
        toks = [re.sub(r"[^\w']", "", p.lower()) for p in phrase.split()]; seen = 0
        for i in range(len(self._norm) - len(toks) + 1):
            if self._norm[i:i + len(toks)] == toks:
                seen += 1
                if seen == occurrence: return i, len(toks)
        raise KeyError(f"phrase {phrase!r} (occurrence {occurrence}) not in transcript")

    def start(self, phrase, occurrence=1): i, _ = self.find(phrase, occurrence); return self.words[i]["start"]
    def end(self, phrase, occurrence=1): i, n = self.find(phrase, occurrence); return self.words[i + n - 1]["end"]

    @property
    def frame_accurate(self):
        """True only for provider timestamps; estimated timing must not be advertised as synchronised."""
        return self.source == "provider"
