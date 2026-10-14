"""Word-synchronised English captions in five styles, plus the rule-based style planner (VISUAL_REF_001 bottom captions, VISUAL_REF_002 kinetic type).

  A  clean documentary   restrained: the phrase fades in whole, high readability (long-form default)
  B  dynamic kinetic     words appear on their own timestamps; important words enlarge and take the accent colour
  C  high impact         bold caps, scale pop with a colour-offset duplicate, short phrase; rare (rate-limited by the planner)
  D  data emphasis       numbers, years (underline sweep), percentages and place names get a highlight (never a count-up: subtitles show the spoken words)
  E  cinematic minimal   small, low, letter-spaced, fade only - for visually busy shots

Timing comes ONLY from the words passed in. `Cues`-style provider timestamps give frame-accurate sync; estimated ones are flagged by the caller
(`source`) and the manifest says so. Cards never overlap in time, the layout is fixed from the full card (no jumping) and every box is registered
for QA (collision / outside-frame)."""
# effect-reuse-checked: yt-captions builds SRT/VTT files and yt-render burns one static style; the Dubai engine's ASS cues are episode code. This is the first
# shared word-timed, multi-style caption renderer (docs/references/VISUAL_EFFECT_CATALOG.md VE-20 was PARTIALLY_IMPLEMENTED).
import math
import re
from . import easing as E
from . import kinetic as K
from .layers import Overlay

STYLES = ("A", "B", "C", "D", "E")
ACCENT = (255, 194, 71)          # OrbitalAtlas amber
DATA = (92, 225, 230)            # OrbitalAtlas cyan
INK = (255, 255, 255)
_NUM = re.compile(r"^\$?\d[\d,]*(\.\d+)?%?$")
_YEAR = re.compile(r"^(1[5-9]\d\d|20\d\d)$")


def clean(w): return re.sub(r"^[^\w$]+|[^\w%]+$", "", w)


def is_year(w): return bool(_YEAR.match(clean(w)))
def is_number(w): return bool(_NUM.match(clean(w))) and not is_year(w)


STARTERS = {"from", "a", "an", "and", "but", "of", "to", "in", "on", "at", "with", "by", "for", "that", "which", "it", "this", "now"}


def _glued(prev, w):
    """words that must stay on one card: the parts of a place name, 'July 2022', a number and its unit."""
    if prev.get("place") and prev.get("place") == w.get("place"): return True
    p, n = clean(prev["text"]).lower(), clean(w["text"]).lower()
    return (p in ("january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december") and is_year(w["text"])) or \
           (is_number(prev["text"]) and n in ("km", "kilometers", "kilometres", "miles", "feet", "meters", "percent", "million", "billion", "acres", "square"))


def make_cards(words, max_words=6, max_chars=40, max_gap=0.5, min_words=1):
    """group words into caption cards: break after sentence/clause punctuation and long pauses; on overflow break at the best nearby point (after a comma or
    before a function word) and never inside a place name, a date or a number + unit; a 1-2 word tail is merged into the previous card when it fits.
    Each card = {'words': [word dicts], 't0', 't1'}; the word dicts keep any extra keys (emph, kind)."""
    cards, cur = [], []
    def flush(n=None):
        nonlocal cur
        n = len(cur) if n is None else n
        if n > 0: cards.append(dict(words=cur[:n], t0=cur[0]["start"], t1=cur[n - 1]["end"])); cur = cur[n:]
    def too_long(ws): return len(ws) > max_words or sum(len(x["text"]) + 1 for x in ws) - 1 > max_chars
    for w in words:
        if cur and w["start"] - cur[-1]["end"] > max_gap: flush()
        cur.append(w)
        if too_long(cur):
            # best break: after the last comma, else before the last starter word, never inside a glued group; fall back to breaking before this word
            best = None
            for k in range(len(cur) - 1, 0, -1):
                if _glued(cur[k - 1], cur[k]): continue
                if cur[k - 1]["text"].endswith(",") or clean(cur[k]["text"]).lower() in STARTERS: best = k; break
            if best is None:
                best = next((k for k in range(len(cur) - 1, 0, -1) if not _glued(cur[k - 1], cur[k])), len(cur) - 1)
            flush(best)
        if re.search(r"[.!?;:]$", cur[-1]["text"]) or (re.search(r",$", cur[-1]["text"]) and len(cur) >= 3): flush()
    flush()
    out = []
    for c in cards:                                      # merge a tiny tail into the previous card
        if out and len(c["words"]) <= 2 and c["t0"] - out[-1]["t1"] <= max_gap and not re.search(r"[.!?]$", out[-1]["words"][-1]["text"]) and not too_long(out[-1]["words"] + c["words"][:0] + c["words"]) :
            out[-1]["words"] += c["words"]; out[-1]["t1"] = c["t1"]
        else: out.append(c)
    return out


def plan_styles(cards, mode="long", complexity=None, impact=None, default=None, max_impact_per_min=2.0, min_run=2):
    """choose a style per card from meaning, pace and visual complexity. Deterministic.
    complexity: callable(t0, t1) -> 0..1 or None; impact: set of card indices flagged as a revelation/emotional statement.
    Rules (first match): busy picture -> E; flagged statement (<= 5 words, within the rate limit) -> C; data words present -> D;
    fast speech in a Short -> B; else the default (A for long-form, B for Shorts). Hysteresis: a plain style (A/B/E) is kept for at least
    `min_run` cards so the look does not flicker; C and D are event styles and never extend the run."""
    default = default or ("A" if mode == "long" else "B"); impact = impact or set(); out = []; last_c = []; run = 0; cur = default
    for i, c in enumerate(cards):
        ws = [clean(w["text"]) for w in c["words"]]; dur = max(c["t1"] - c["t0"], 0.2); wps = len(ws) / dur
        busy = complexity(c["t0"], c["t1"]) if complexity else 0.0
        has_data = any(is_year(x["text"]) or is_number(x["text"]) or x.get("kind") in ("year", "number", "place") for x in c["words"])
        last_c = [t for t in last_c if c["t0"] - t < 60.0]
        if busy > 0.7: s = "E"
        elif i in impact and len(ws) <= 6 and len(last_c) < max_impact_per_min: s = "C"; last_c.append(c["t0"])
        elif has_data: s = "D"
        elif mode == "short" and wps > 3.0: s = "B"
        else: s = default
        if s in ("A", "B", "E"):
            if run > 0 and run < min_run and cur in ("A", "B", "E") and cur != s: s = cur; run += 1
            else: run = 1 if s != cur else run + 1
            cur = s
        out.append(s)
    return out


def _wrap(words, px, weight, maxw, gap, ws=None):
    """balanced greedy wrap into <= 2 lines; returns [[word indices...], line widths]. `ws` overrides the measured word widths (style D: wider special words)."""
    ws = ws or [K.width(w["text"], px, weight) for w in words]; sp = px * gap
    total = sum(ws) + sp * (len(ws) - 1)
    if total <= maxw or len(ws) < 2: return [list(range(len(ws)))], [total]
    best = None
    for k in range(1, len(ws)):
        a = sum(ws[:k]) + sp * (k - 1); b = sum(ws[k:]) + sp * (len(ws) - k - 1)
        sc = max(a, b)
        if best is None or sc < best[0]: best = (sc, k, a, b)
    _, k, a, b = best
    return [list(range(k)), list(range(k, len(ws)))], [a, b]


class WordCaptions(Overlay):
    """caption overlay. `cards` from make_cards, `styles` from plan_styles (or a single letter). Draws on the UI layer (never camera-blurred)."""
    layer = "ui"; cls = "TEXT"

    def __init__(self, cards, styles="A", position=None, scale=1.0, hold=0.30, lead=0.05, accent=ACCENT, data=DATA, source="provider", hidden=()):
        self.cards = cards; self.hold, self.lead, self.accent, self.data = hold, lead, accent, data
        self.styles = [styles] * len(cards) if isinstance(styles, str) else list(styles)
        assert len(self.styles) == len(cards) and all(s in STYLES for s in self.styles)
        self.position, self.scale, self.source = position, scale, source
        self.hidden = set(hidden)            # cards whose content is carried by a focus graphic (number card, impact card): not drawn, no duplicate
        # a card ends when the next starts (no overlap) or after `hold`
        self.ends = [min(c["t1"] + hold, cards[i + 1]["t0"] - lead - 0.01 if i + 1 < len(cards) else 1e9) for i, c in enumerate(cards)]
        self.ends = [min(max(e, c["t1"] + 0.05), cards[i + 1]["t0"] - lead - 0.005 if i + 1 < len(cards) else 1e9) for i, (e, c) in enumerate(zip(self.ends, cards))]   # never overlaps the next card

    def active(self, t):
        for i, c in enumerate(self.cards):
            if c["t0"] - self.lead <= t < self.ends[i]: return i
        return None

    def describe(self):
        d = super().describe(); d.update(cards=len(self.cards), styles="".join(self.styles), timing=self.source, hidden=sorted(self.hidden)); return d

    def draw(self, ctx):
        i = self.active(ctx.t)
        if i is None or i in self.hidden: return
        c, s = self.cards[i], self.styles[i]; W, H = ctx.size; vertical = H > W
        base = H * (0.034 if vertical else 0.052) * self.scale
        cy = self.position[1] * H if self.position else (H * 0.70 if vertical else H * 0.845)
        cx = self.position[0] * W if self.position else W / 2
        layer, reg = ctx.ui, ctx.reg; t = ctx.t; ws = c["words"]
        {"A": self._a, "B": self._b, "C": self._c, "D": self._d, "E": self._e}[s](layer, reg, t, c, ws, base, cx, cy, W, H, i)

    # ---- layout helper: positions of each word for a centred, wrapped card
    def _layout(self, ws, px, weight, cx, cy, W, gap=0.26, line_h=1.18, widths=None):
        lines, wid = _wrap(ws, px, weight, W * 0.82, gap, widths); sp = px * gap; pos = {}
        n = len(lines); y0 = cy - (n - 1) * px * line_h / 2
        for li, idx in enumerate(lines):
            x = cx - wid[li] / 2
            for j in idx:
                pos[j] = (x, y0 + li * px * line_h); x += (widths[j] if widths else K.width(ws[j]["text"], px, weight)) + sp
        return pos

    def _a(self, layer, reg, t, c, ws, px, cx, cy, W, H, i):
        u = E.out_cubic(E.seg(t, c["t0"] - self.lead, c["t0"] + 0.12)) * (1 - E.smooth(E.seg(t, self.ends[i] - 0.12, self.ends[i])))
        pos = self._layout(ws, px, "bold", cx, cy, W)
        for j, w in enumerate(ws):
            K.draw_text(layer, pos[j], w["text"], px, INK, "bold", u, shadow=0.07, stroke=max(1, int(px * 0.035)), stroke_color=(0, 0, 0))
        self._reg(reg, ws, pos, px, "bold", u, f"cap{i}")

    def _b(self, layer, reg, t, c, ws, px, cx, cy, W, H, i):
        pos = self._layout(ws, px, "bold", cx, cy, W); out = 1 - E.smooth(E.seg(t, self.ends[i] - 0.1, self.ends[i]))
        for j, w in enumerate(ws):
            u = E.seg(t, w["start"] - 0.02, w["start"] + 0.16)
            if u <= 0: continue
            emph = bool(w.get("emph")); big = 1.0 + (0.2 * E.out_back(u, 2.0) if emph else 0.0) if u < 1 else (1.2 if emph else 1.0)
            col = self.accent if emph else INK
            K.draw_text(layer, (pos[j][0], pos[j][1] + (1 - E.out_cubic(u)) * px * 0.3 - (big - 1) * px * 0.3), w["text"], px * big, col, "heavy" if emph else "bold",
                        E.out_cubic(u) * out, shadow=0.07, stroke=max(1, int(px * 0.035)), stroke_color=(0, 0, 0))
        self._reg(reg, ws, pos, px, "bold", out, f"cap{i}")

    def _c(self, layer, reg, t, c, ws, px, cx, cy, W, H, i):
        text = " ".join(clean(w["text"]) for w in ws).upper(); big = px * 1.75
        while K.width(text, big, "black") > W * 0.86 and big > px: big *= 0.93
        y = cy - px * 1.1
        K.duplicate_offset(layer, (cx, y), text, big, t, c["t0"] - self.lead, front=INK, back=self.accent, offset=0.05, dur=0.22, anchor="center", reg=reg, group=f"cap{i}")

    def _d(self, layer, reg, t, c, ws, px, cx, cy, W, H, i):
        sp_ = [is_year(w["text"]) or is_number(w["text"]) or w.get("kind") in ("year", "number", "place") for w in ws]
        widths = [K.width(w["text"], px * 1.12, "black") * 1.02 if s_ else K.width(w["text"], px, "bold") for w, s_ in zip(ws, sp_)]
        pos = self._layout(ws, px, "bold", cx, cy, W, widths=widths); out = 1 - E.smooth(E.seg(t, self.ends[i] - 0.1, self.ends[i]))
        for j, w in enumerate(ws):
            u = E.seg(t, w["start"] - 0.02, w["start"] + 0.18)
            if u <= 0: continue
            txt = w["text"]; x, y = pos[j]; wd = K.width(txt, px, "heavy")
            special = is_year(txt) or is_number(txt) or w.get("kind") in ("year", "number", "place")
            if not special:
                K.draw_text(layer, (x, y), txt, px, INK, "bold", E.out_cubic(u) * out, shadow=0.07, stroke=max(1, int(px * 0.035)), stroke_color=(0, 0, 0)); continue
            # no count-up in captions: a subtitle shows the spoken words exactly (count-up lives in typeset.NumberCard)
            plate = K.draw_text(layer, (x, y), txt, px * 1.12, self.data if w.get("kind") != "place" else self.accent, "black", E.out_cubic(u) * out, shadow=0.07, stroke=max(1, int(px * 0.04)), stroke_color=(0, 0, 0))
            if is_year(w["text"]) and plate:             # underline sweep
                sw = E.out_expo(E.seg(t, w["start"] + 0.05, w["start"] + 0.4)); d = _draw(layer)
                d.rectangle([plate[0], plate[3] - px * 0.12, plate[0] + (plate[2] - plate[0]) * sw, plate[3] - px * 0.06], fill=self.data + (int(255 * out),))
        self._reg(reg, ws, pos, px, "heavy", out, f"cap{i}")

    def _e(self, layer, reg, t, c, ws, px, cx, cy, W, H, i):
        px = px * 0.72; u = E.out_cubic(E.seg(t, c["t0"] - self.lead, c["t0"] + 0.25)) * (1 - E.smooth(E.seg(t, self.ends[i] - 0.2, self.ends[i]))) * 0.88
        text = " ".join(w["text"] for w in ws); w_ = K.width(text, px, "regular", 0.06)
        while w_ > W * 0.8 and px > 12: px *= 0.93; w_ = K.width(text, px, "regular", 0.06)
        b = K.draw_text(layer, (cx, cy + px * 0.9), text, px, (235, 240, 246), "regular", u, track=0.06, anchor="center", shadow=0.08)
        if b: reg.add(f"cap{i}", b, u)

    def _reg(self, reg, ws, pos, px, weight, alpha, group):
        if not pos: return
        x0 = min(p[0] for p in pos.values()); y0 = min(p[1] for p in pos.values()); x1 = max(pos[j][0] + K.width(ws[j]["text"], px, weight) for j in pos); y1 = max(p[1] for p in pos.values()) + px * 1.25
        reg.add(group, (x0, y0, x1, y1), alpha)


def _draw(layer):
    from PIL import ImageDraw
    return ImageDraw.Draw(layer, "RGBA")


def _count_up(txt, k):
    """interpolate a number string towards its final value keeping its format (thousands commas, decimals, % and $)."""
    m = re.match(r"^(\$?)([\d,]*)(\.\d+)?(%?)$", clean(txt) if not txt.startswith("$") else txt)
    if not m: return txt
    pre, ip, dec, suf = m.group(1), m.group(2), m.group(3) or "", m.group(4)
    val = float((ip.replace(",", "")) + (dec or "")) * k; nd = len(dec) - 1 if dec else 0
    s = f"{val:,.{nd}f}" if "," in ip else f"{val:.{nd}f}"
    return pre + s + suf
