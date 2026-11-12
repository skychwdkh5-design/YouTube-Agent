"""Find narration times by phrase in the provider word timings (yt-voice/1 JSON)."""
import json
import re


def norm(s):
    s = s.lower().replace('’', "'").replace('‘', "'")
    return re.sub(r"[^a-z0-9' -]", '', s).strip()


class Cues:
    def __init__(self, words_json):
        d = json.load(open(words_json))
        self.words = d['words']
        self.duration = float(d.get('duration') or self.words[-1]['end'])
        self.toks = [norm(w['text']) for w in self.words]

    def _find(self, phrase, after=0.0):
        p = [norm(x) for x in phrase.split()]
        for i in range(len(self.toks) - len(p) + 1):
            if self.words[i]['start'] + 1e-6 < after:
                continue
            if all(self.toks[i + k].strip("'") == p[k].strip("'") for k in range(len(p))):
                return i, i + len(p) - 1
        raise KeyError(f'phrase not found after {after:.2f}s: {phrase!r}')

    def at(self, phrase, after=0.0):
        return self.words[self._find(phrase, after)[0]]['start']

    def end(self, phrase, after=0.0):
        return self.words[self._find(phrase, after)[1]]['end']

    def last_end(self):
        return self.words[-1]['end']
