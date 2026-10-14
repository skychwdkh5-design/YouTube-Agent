"""Layers that INTERACT (v2c): text that leaves the subtitle line and becomes part of the map, labels that float above the map with parallax,
depth dust, a digital punch-in on emphasis, and two date components that can never be confused:

  KeywordLift   a keyword is lifted out of the caption line (same position the caption uses), flies on a curve to its map anchor while it scales and
                tilts, and lands as an anchored label that follows the camera (text -> map composition transition)
  FloatingLabel an anchored label on a higher 'depth' than the map: it moves slightly more than the map when the camera moves (parallax)
  ParallaxDust  sparse soft motes fixed in WORLD space at several depths; camera moves produce parallax (depth cue), low alpha
  Punch         Scene wrapper: short digital punch-in (1.0 -> 1+amount -> settle) on emphasis words; frame-space, honest (no new pixels)
  ImageStamp    the date of the PICTURE: small mono plate 'IMAGE · <sensor> · <month year>' with a viewfinder mark, cyan
  EventYear     the year of an EVENT spoken in the narration: large amber outline-to-fill year + the narration words; never says IMAGE
Date rule: an EventYear and the ImageStamp never share a style or a position, and the director checks that the stamp equals the asset date."""
# effect-reuse-checked: fx.MarkerPin/CalloutPanel anchor text to a place but nothing moved a caption word to the map, had parallax, a punch-in wrapper
# or separated image dates from event years (v2b showed both as the same YearTag style).
import math
import numpy as np
from PIL import Image, ImageDraw
from . import easing as E
from . import kinetic as K
from . import typeset as TS
from .layers import Overlay

CYAN, AMBER, WHITE = (92, 225, 230), (255, 194, 71), (255, 255, 255)


def parallax(view, p, depth):
    """screen point of source point p for a layer `depth` above the map: further from the centre than the map point (moves more on pans/zooms)."""
    s = view.pt(p); c = np.array([view.W / 2, view.H / 2]); return s + (s - c) * depth


class KeywordLift(Overlay):
    """caption word -> map label. `caps` is the programme's WordCaptions (positions come from it), `t_word` the word start in PROGRAMME time,
    `shot_t0` the shot start in programme time (scene overlays run on shot time). The word copy lands on `anchor` (source px) and stays until t1."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, caps, t_word, text, anchor, shot_t0, t1, color=AMBER, land_px=34, depth=0.05, group=None, label=None):
        self.caps, self.t_word, self.p, self.shot_t0, self.t1, self.color, self.land_px, self.depth = caps, t_word, np.asarray(anchor, float), shot_t0, t1, color, land_px, depth
        self.ij = caps.locate(t_word, text); self.text = (label or text).upper()      # `text` = the caption word to lift, `label` = what lands (e.g. the full place name)
        self.group = group or f"lift_{self.text}"
        if self.ij[0] is not None:                                     # tell the caption: every word of the label that is in the same card is dimmed once it leaves
            card = caps.cards[self.ij[0]]["words"]; n = len((label or text).split())
            for jj in range(self.ij[1], min(len(card), self.ij[1] + n)): caps.lifted[(self.ij[0], jj)] = t_word + 0.15
    def draw(self, ctx):
        tg = ctx.t + self.shot_t0; t0 = self.t_word + 0.05
        if tg < t0 or tg > self.t1 + 0.3: return
        W, H = ctx.size; k = H / 1080; box = self.caps.word_box(ctx.size, *self.ij) if self.ij[0] is not None else None
        start = np.array([(box[0] + box[2]) / 2, (box[1] + box[3]) / 2]) if box else np.array([W / 2, H * 0.85])
        end = parallax(ctx.view, self.p, self.depth) + np.array([0, -self.land_px * k * 1.4])
        u = E.seg(tg, t0 + 0.12, t0 + 0.75); e = E.in_out_cubic(u); o = 1 - E.smooth(E.seg(tg, self.t1, self.t1 + 0.3))
        mid = (start + end) / 2 + np.array([0, -0.18 * H]); pt = (1 - e) ** 2 * start + 2 * (1 - e) * e * mid + e ** 2 * end   # quadratic arc
        cap_px = (box[3] - box[1]) / 1.2 if box else 0.052 * H; px = E.lerp(cap_px * 1.15, self.land_px * k, e)
        lift = E.out_back(E.seg(tg, t0, t0 + 0.14), 2.0)
        if u <= 0: px = cap_px * (1 + 0.15 * lift)
        w = K.width(self.text, px, "black"); x, y = pt[0] - w / 2, pt[1] - px * 0.62
        if e >= 1:                                                        # landed: leader tick to the anchor
            d = ImageDraw.Draw(ctx.ui, "RGBA"); a = ctx.view.pt(self.p); col = tuple(self.color) + (int(230 * o),)
            d.line([(pt[0], pt[1] + px * 0.65), tuple(a)], fill=col, width=max(2, int(2 * k)))
        if e >= 1:                                                         # landed: readable over any annotation (dark outline), amber like the region accents
            K.draw_text(ctx.ui, (x, y), self.text, px, self.color, "black", o, shadow=0.06, stroke=max(2, int(px * 0.09)), stroke_color=(8, 10, 14))
        else:
            TS.put(ctx.ui, self.text, x, y, px, "black", self.color, "fill", o, 1.0, 0.0, None, None, None, px * 0.06 if 0 < u < 1 else 0.0)
        ctx.reg.add(self.group, (x, y, x + w, y + px * 1.25), o)
    def describe(self): return dict(super().describe(), effect="keyword_lift", word=self.text)


class FloatingLabel(Overlay):
    """name label above its anchor on a parallax depth, with a hairline to the point; slides up into place."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, p, text, t0, t1, depth=0.06, px=26, color=WHITE, accent=CYAN, group=None):
        self.p, self.text, self.t0, self.t1, self.depth, self.px, self.color, self.accent = np.asarray(p, float), text, t0, t1, depth, px, color, accent
        self.group = group or f"float_{text}"
    def draw(self, ctx):
        t = ctx.t
        if t < self.t0 or t > self.t1 + 0.3: return
        k = ctx.size[1] / 1080; px = self.px * k; a = ctx.view.pt(self.p); s = parallax(ctx.view, self.p, self.depth) + np.array([0, -px * 2.2])
        u = E.out_expo(E.seg(t, self.t0, self.t0 + 0.4)); o = 1 - E.smooth(E.seg(t, self.t1, self.t1 + 0.3))
        d = ImageDraw.Draw(ctx.ui, "RGBA"); d.line([tuple(a), (s[0], s[1] + px * 1.3)], fill=tuple(self.accent) + (int(200 * o * u),), width=max(1, int(1.5 * k)))
        w = K.width(self.text.upper(), px, "heavy", 0.1); x = s[0] - w / 2; y = s[1] + (1 - u) * px
        b = K.draw_text(ctx.ui, (x, y), self.text.upper(), px, self.color, "heavy", o * u, track=0.1, shadow=0.08, stroke=max(1, int(1.2 * k)))
        if b: ctx.reg.add(self.group, b, o * u)
    def describe(self): return dict(super().describe(), effect="floating_label", depth=self.depth)


class ParallaxDust(Overlay):
    """world-anchored motes at three depths over the image extent (seeded): pans and zooms move near motes faster than the map -> depth."""
    layer = "ui"; cls = "DECOR"
    def __init__(self, extent, t0, t1, n=90, seed=11, alpha=0.35, color=(220, 235, 255)):
        r = np.random.RandomState(seed); x0, y0, x1, y1 = extent
        self.p = np.c_[x0 + r.rand(n) * (x1 - x0), y0 + r.rand(n) * (y1 - y0)]; self.depth = r.choice([0.05, 0.12, 0.22], n); self.sz = 0.6 + r.rand(n)
        self.t0, self.t1, self.alpha, self.color = t0, t1, alpha, color
    def draw(self, ctx):
        a0 = self.alpha * E.smooth(E.seg(ctx.t, self.t0, self.t0 + 0.5)) * (1 - E.smooth(E.seg(ctx.t, self.t1 - 0.5, self.t1)))
        if a0 <= 0.01: return
        k = ctx.size[1] / 1080; d = ImageDraw.Draw(ctx.ui, "RGBA"); W, H = ctx.size
        for p, dp, sz in zip(self.p, self.depth, self.sz):
            s = parallax(ctx.view, p, dp)
            if -10 < s[0] < W + 10 and -10 < s[1] < H + 10:
                r = (1.2 + 3.0 * dp * 4) * sz * k; d.ellipse([s[0] - r, s[1] - r, s[0] + r, s[1] + r], fill=self.color + (int(255 * a0 * (0.3 + dp * 3)),))
    def describe(self): return dict(super().describe(), effect="parallax_dust")


class ImageStamp(Overlay):
    """date of the picture on screen. Always says IMAGE; cyan mono plate top-left with a viewfinder mark. Its text comes from the asset metadata."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, text, t0, t1, xy=(0.035, 0.06), group="image_stamp"):
        self.text, self.t0, self.t1, self.xy, self.group = text.upper(), t0, t1, xy, group
    def draw(self, ctx):
        t = ctx.t
        if t < self.t0 or t > self.t1 + 0.3: return
        W, H = ctx.size; k = H / 1080; px = 19 * k; x, y = self.xy[0] * W, self.xy[1] * H; o = 1 - E.smooth(E.seg(t, self.t1, self.t1 + 0.3))
        u = E.out_expo(E.seg(t, self.t0, self.t0 + 0.35)); s = "IMAGE · " + self.text; n = int(len(s) * E.seg(t, self.t0 + 0.1, self.t0 + 0.6))
        w = K.width(s, px, "bold", 0.16) + px * 2.4; d = ImageDraw.Draw(ctx.ui, "RGBA"); col = CYAN + (int(255 * o),)
        d.rectangle([x, y, x + w * u, y + px * 1.9], fill=(6, 10, 16, int(170 * o)))
        b = px * 0.45; cx, cy = x + px * 0.9, y + px * 0.95                  # viewfinder corners
        for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            d.line([(cx + dx * b, cy + dy * b * 0.4), (cx + dx * b, cy + dy * b), (cx + dx * b * 0.4, cy + dy * b)], fill=col, width=max(1, int(2 * k)))
        K.draw_text(ctx.ui, (x + px * 1.9, y + px * 0.38), s[:n], px, CYAN, "bold", o, track=0.16)
        ctx.reg.add(self.group, (x, y, x + w, y + px * 1.9), o * u)
    def describe(self): return dict(super().describe(), effect="image_stamp", text=self.text)


class EventYear(Overlay):
    """year of a historical EVENT (amber, top-right): the year draws as an outline and fills, the narration words underneath, a tick line."""
    layer = "ui"; cls = "TEXT"
    def __init__(self, year, words, t0, t1, xy=(0.70, 0.07), px=0.085, group="event_year"):
        self.year, self.words, self.t0, self.t1, self.xy, self.px, self.group = str(year), words.upper(), t0, t1, xy, px, group
    def draw(self, ctx):
        t = ctx.t
        if t < self.t0 or t > self.t1 + 0.3: return
        W, H = ctx.size; px = self.px * H; x, y = self.xy[0] * W, self.xy[1] * H; o = 1 - E.smooth(E.seg(t, self.t1, self.t1 + 0.3))
        TS.animate_word(ctx.ui, self.year, x, y, px, t, self.t0, "outline_fill", "black", AMBER, dur=0.3)
        lw = K.width(self.year, px, "black"); f = E.out_expo(E.seg(t, self.t0 + 0.1, self.t0 + 0.5)); d = ImageDraw.Draw(ctx.ui, "RGBA")
        d.line([(x, y + px * 1.42), (x + lw * f, y + px * 1.42)], fill=AMBER + (int(255 * o),), width=max(2, int(px * 0.03)))
        n = int(len(self.words) * E.seg(t, self.t0 + 0.2, self.t0 + 0.7))
        K.draw_text(ctx.ui, (x, y + px * 1.55), self.words[:n], max(12.0, px * 0.27), WHITE, "bold", o, track=0.12, shadow=0.08)
        if o < 1:
            ImageDraw.Draw(ctx.ui, "RGBA")
        ctx.reg.add(self.group, (x, y, x + max(lw, K.width(self.words, max(12.0, px * 0.27), "bold", 0.12)), y + px * 1.95), o)
    def describe(self): return dict(super().describe(), effect="event_year", year=self.year)


class Punch:
    """Scene wrapper: digital punch-in about the frame centre at given programme-local times: [(t, amount)]; envelope 0.08 s up, 0.6 s settle."""
    def __init__(self, scene, hits):
        self.scene, self.hits = scene, sorted(hits); self.size, self.name, self.reg = scene.size, scene.name, scene.reg
    @property
    def start(self): return self.scene.start
    @property
    def end(self): return self.scene.end
    @property
    def camera(self): return self.scene.camera
    def factor(self, t):
        f = 1.0
        for th, a in self.hits:
            if th - 0.1 <= t <= th + 0.8: f += a * (E.out_cubic(E.seg(t, th, th + 0.08)) * (1 - E.in_out_cubic(E.seg(t, th + 0.12, th + 0.75))))
        return f
    def render(self, t, **kw):
        fr = self.scene.render(t, **kw); f = self.factor(t)
        if f <= 1.0005: return fr
        W, H = fr.size; w, h = W / f, H / f
        return fr.transform((W, H), Image.EXTENT, ((W - w) / 2, (H - h) / 2, (W + w) / 2, (H + h) / 2), Image.BICUBIC)
    def manifest(self):
        m = list(self.scene.manifest()) if hasattr(self.scene, "manifest") else []
        return m + [dict(type="Punch", cls="PRESENTATION", hits=self.hits)]
