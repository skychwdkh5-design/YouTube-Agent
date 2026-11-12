"""Voyager 1 (EP013) scene graphics, after the owner's motion.js reference (1280x720 design space).
Layouts leave room for ATLAS (host layer) and keep labels/credits clear of him."""
import math
import os

from engine_path import *            # noqa: F401,F403  (adds engine to sys.path)
from gfx import Frame, PAL, rng, lerp, smooth, clamp, Video

SRC = os.environ.get('VOYAGER_SRC', '/mnt/project-files/voyager/EP013/src')
A = lambda n: os.path.join(SRC, 'assets', n)

# palette of the approved SIGNAL LOST poster: cream, signal red-orange, warm black
PAL.update(ice=(239, 226, 196), amber=(242, 112, 58), red=(232, 62, 40), paper=(247, 238, 222))
ICE, AMBER, RED, PAPER = PAL['ice'], PAL['amber'], PAL['red'], PAL['paper']


# ------------------------------------------------------------------ 1. cover / probe
def cover(f, t, pulse=0.0, text_a=1.0, zoom=0.0, x_shift=0.0, label=True):
    """Frame 0 composition (cover A). pulse: 0..1 along the link line."""
    f.image(A('voyager.jpg'), 0, 0, 1280, 720, 1 + 0.09 * zoom, 0.72, 0.43)
    f.shade([(0, '#0a0605f7'), (0.47, '#041321bc'), (0.77, '#04132100')])
    if text_a > 0.01:
        x = 57 - x_shift
        f.group(text_a)
        f.kick('N A S A   /   V O Y A G E R  1', x, 83)
        f.big('48', x, 300, 190)
        f.big('HOURS', x + 6, 384, 80)
        f.text('FOR A ROUND TRIP', x + 9, 430, 21, 'ice', 'mono')
        f.end()
    f.line([(68, 554), (1190, 554)], (132, 196, 233, 99), 2)
    px = lerp(73, 1170, pulse)
    f.glow(px, 554, 44, ICE)
    f.circle(px, 554, 4, 'ice')
    if label:
        f.footer('ARTIST CONCEPT', 'NASA / JPL-CALTECH')


# ------------------------------------------------------------------ 2. signal diagram
EARTH_X, PROBE_X, LINK_Y = 470, 1150, 290


def earth(f, x, y, r=50):
    f.glow(x, y, r * 1.8, (232, 62, 40), 0.55)
    f.circle(x, y, r, (52, 30, 24), ICE, 2)
    for i in range(6):
        yy = y - r * 0.74 + i * r * 0.32
        f.line([(x - r * 0.86, yy + 4), (x + r * 0.1, yy - 2), (x + r * 0.78, yy + 6)], (239, 226, 196, 70), 4.2)


def probe_dot(f, x, y):
    f.circle(x, y, 26, (40, 26, 20), (239, 226, 196), 2)
    f.circle(x, y, 7, 'ice')


def diagram_bg(f, t, kick='SIGNAL TRAVEL TIME  /  EARTH ↔ VOYAGER 1'):
    f.background('#1f1713', '#0a0706')
    f.starfield(t)
    f.grid(50, '#efe2c40c', t * 9)
    f.kick(kick)


def signal(f, t, leg, p, title=None, sub=None, title_a=1.0):
    """leg 0: outbound (ice), leg 1: reply (amber). p: pulse progress 0..1."""
    diagram_bg(f, t)
    ax, bx, y = EARTH_X, PROBE_X, LINK_Y
    px = lerp(bx, ax, p) if leg else lerp(ax, bx, p)
    col = AMBER if leg else ICE
    f.line([(ax, y), (bx, y)], (200, 180, 150, 110), 2, dash=(8, 12))
    f.line([(bx if leg else ax, y), (px, y)], col, 3)
    earth(f, ax, y)
    probe_dot(f, bx, y)
    f.glow(px, y, 55, col)
    f.circle(px, y, 7, col)
    f.text('EARTH', ax, y + 88, 21, 'paper', 'mono', 'center')
    f.text('VOYAGER 1', bx, y + 88, 21, 'paper', 'mono', 'center')
    if title:
        f.text(title, 810, 175, 66, col, 'sans', 'center', alpha=title_a)
    if sub:
        f.text(sub, 810, 440, 21, 'paper', 'mono', 'center', alpha=title_a)
    f.footer('SCHEMATIC  /  NOT TO SCALE')


# ------------------------------------------------------------------ 3. listening windows
def dates(f, t, photo, z, alphas, states, credit, kick='DEEP SPACE NETWORK  /  OCTOBER 2026', x0=470):
    """photo full frame; date rows on the RIGHT half (ATLAS stands left)."""
    f.image(photo, 0, 0, 1280, 720, 1.01 + 0.08 * z, 0.57, 0.46)
    f.shade([(0, '#0a060515'), (0.37, '#0a0605cc'), (1, '#0a0605f8')])
    f.kick(kick, x0 + 12, 65)
    labels = ['OCT 18', 'OCT 19', 'OCT 20']
    for i, a in enumerate(alphas):
        if a <= 0.01:
            continue
        y = 190 + 112 * i
        f.group(a)
        f.rect(x0, y - 49, 640, 80, (16, 10, 8, 216), (239, 226, 196, 69))
        f.text(labels[i], x0 + 25, y + 3, 28, 'paper', 'mono')
        ok = states[i]
        f.text('SIGNAL BACK' if ok else 'NO SIGNAL', x0 + 225, y + 4, 34, 'ice' if ok else 'red', 'sans')
        f.circle(x0 + 605, y - 7, 5, 'ice' if ok else 'red')
        f.end()
    f.footer('ARCHIVE PHOTO', credit)


# ------------------------------------------------------------------ 4. thrusters
def thrusters(f, t, off_a, on_a, auto_a, plaque_a, photo_a=1.0):
    f.background('#1f1713', '#0a0706')
    f.starfield(t * 0.3, 60)
    f.kick('VOYAGER 1  /  THRUSTERS', 470, 65)
    # archive photo inset (small source, shown at modest size)
    if photo_a > 0:
        f.rect(468, 92, 404, 229, None, (239, 226, 196, 70), 1, alpha=photo_a)
        f.image(A('voyager_archive.jpg'), 470, 94, 400, 225, 1.0, 0.5, 0.5, alpha=photo_a)
        f.text('ARTIST CONCEPT  ·  NASA/JPL-CALTECH', 470, 340, 13, (217, 225, 230), 'mono_r', alpha=photo_a)
    # schematic: two thruster groups
    gx = [960, 1135]
    names = ['THRUSTER GROUP', 'BACKUP GROUP']
    for k, x in enumerate(gx):
        on = (1 - off_a) if k == 0 else on_a
        col = ICE if on > 0.5 else (120, 130, 140)
        f.rect(x - 70, 120, 140, 150, (20, 13, 10, 220), (239, 226, 196, 60), 1, radius=6)
        for j in range(3):
            cx, cy = x - 40 + j * 40, 175
            f.poly([(cx - 10, cy - 18), (cx + 10, cy - 18), (cx + 16, cy + 18), (cx - 16, cy + 18)], (70, 50, 40, 255))
            if on > 0.02:
                f.glow(cx, cy + 34, 22, col, on)
        f.text(names[k], x, 248, 13, 'paper', 'mono', 'center')
        st = 'ONLINE' if k == 0 else 'STANDBY'
        if k == 0 and off_a > 0.5:
            st = 'OFFLINE'
        if k == 1 and on_a > 0.5:
            st = 'SWITCHED ON'
        f.text(st, x, 300, 18, 'red' if st == 'OFFLINE' else ('ice' if st != 'STANDBY' else (150, 160, 170)), 'mono', 'center')
    if auto_a > 0:
        f.line([(1030, 195), (1065, 195)], ICE, 2, alpha=auto_a)
        f.poly([(1065, 188), (1075, 195), (1065, 202)], (239, 226, 196, int(255 * auto_a)))
        f.text('AUTOMATIC SWITCH', 1047, 352, 16, 'ice', 'mono', 'center', alpha=auto_a)
    if plaque_a > 0:
        f.group(plaque_a)
        f.rect(470, 420, 640, 64, (40, 12, 10, 225), (255, 96, 72, 140), 1)
        f.text('CAUSE UNDER INVESTIGATION', 790, 463, 30, 'red', 'sans', 'center')
        f.end()
    f.footer('SCHEMATIC  /  SIMPLIFIED')


# ------------------------------------------------------------------ 5. round trip timeline
def round_trip(f, t, p_send, p_reply, marks, big_a, loop_p=0.0):
    """Timeline SEND -> ARRIVE -> REPLY RECEIVED, hours 0/24/48 revealed by marks[0..2]."""
    diagram_bg(f, t, 'ONE CONVERSATION WITH VOYAGER 1')
    x0, x1, x2, y = 470, 820, 1170, 280
    f.line([(x0, y), (x2, y)], (200, 180, 150, 100), 2, dash=(8, 12))
    if p_send > 0:
        f.line([(x0, y), (lerp(x0, x1, p_send), y)], ICE, 4)
        f.glow(lerp(x0, x1, p_send), y, 40, ICE)
    if p_reply > 0:
        f.line([(x1, y), (lerp(x1, x2, p_reply), y)], AMBER, 4)
        f.glow(lerp(x1, x2, p_reply), y, 40, AMBER)
    if loop_p > 0:
        f.line([(x0, y + 26), (lerp(x0, x2, loop_p), y + 26)], (239, 226, 196, 150), 2, dash=(4, 8))
        f.text('NEXT COMMAND: THE TRIP STARTS AGAIN', x0, y + 60, 16, 'ice', 'mono', alpha=min(1, loop_p * 3))
    names = [('SEND', 'HOUR 0', ICE), ('ARRIVE', 'HOUR 24', ICE), ('REPLY RECEIVED', 'HOUR 48', AMBER)]
    for k, (x, (a, b, col)) in enumerate(zip((x0, x1, x2), names)):
        m = marks[k]
        f.circle(x, y, 11, (20, 13, 10), col if m > 0.5 else (120, 140, 155), 2)
        if m > 0:
            f.circle(x, y, 5, col, alpha=m)
            f.text(a, x, y - 34, 19, 'paper', 'mono', 'center', alpha=m)
            f.text(b, x, y + 44, 25, col, 'sans', 'center', alpha=m)
    if big_a > 0:
        f.text('48 HOURS', 820, 190, 62, 'amber', 'sans', 'center', alpha=big_a)
        f.text('OF TRAVEL TIME ALONE', 820, 420, 22, 'paper', 'mono', 'center', alpha=big_a)
    f.footer('SCHEMATIC  /  DISTANCES NOT TO SCALE  /  48 H WITH AN IMMEDIATE REPLY')


def distance(f, t, pull, miles_a, lday_a, nomark_a):
    """Pull back from the link to the ~16 billion miles / one light-day scale."""
    diagram_bg(f, t, 'NOVEMBER 18, 2026  /  EARTH ↔ VOYAGER 1')
    ex = lerp(500, 470, pull)
    vx = lerp(900, 1180, pull)
    y = 300
    f.line([(ex, y), (vx, y)], (239, 226, 196, 160), 2)
    earth(f, ex, y, lerp(40, 14, pull))
    probe_dot(f, vx, y)
    if miles_a > 0:
        f.text('~16 BILLION MILES', (ex + vx) / 2, 220, 52, 'paper', 'sans', 'center', alpha=miles_a)
        f.text('≈ 26 BILLION KM', (ex + vx) / 2, 252, 18, (200, 210, 220), 'mono', 'center', alpha=miles_a)
    if lday_a > 0:
        f.text('= ONE LIGHT-DAY', (ex + vx) / 2, 372, 40, 'ice', 'sans', 'center', alpha=lday_a)
        f.text('24 HOURS ONE WAY AT THE SPEED OF LIGHT', (ex + vx) / 2, 405, 16, 'paper', 'mono', 'center', alpha=lday_a)
    if nomark_a > 0:
        f.pill('NO MARKER IN SPACE', (ex + vx) / 2 - 120, 470, 'amber')
    f.footer('SCHEMATIC  /  NOT TO SCALE')


# ------------------------------------------------------------------ 6. power swap
def power(f, t, off_p, on_p, warm_a, together_a, less_a, y27_a):
    f.image(A('voyager.jpg'), 0, 0, 1280, 720, 1.05 + 0.03 * smooth(t / 40), 0.72, 0.43)
    f.shade([(0, '#0a0605a0'), (0.35, '#0a0605e6'), (1, '#0a0605f7')])
    f.kick('SEPTEMBER  /  KEEPING VOYAGER 1 WARM', 470, 65)
    for k in range(3):
        y = 130 + k * 92
        # old device
        old_on = 1 - off_p
        f.rect(470, y, 200, 62, (22, 14, 11, 230), (255, 179, 100, 80 + int(120 * old_on)), 1, radius=5)
        f.text('DEVICE', 570, y + 27, 14, (220, 220, 220), 'mono', 'center')
        f.text('ON' if old_on > 0.5 else 'OFF', 570, y + 50, 16, 'amber' if old_on > 0.5 else (140, 145, 150), 'mono', 'center')
        # arrow
        f.line([(690, y + 31), (760, y + 31)], (239, 226, 196, 140), 2)
        f.poly([(760, y + 24), (772, y + 31), (760, y + 38)], (239, 226, 196, 160))
        # replacement
        f.rect(790, y, 240, 62, (22, 14, 11, 230), (239, 226, 196, 60 + int(150 * on_p)), 1, radius=5)
        f.text('LOWER-POWER', 910, y + 27, 14, (220, 220, 220), 'mono', 'center')
        f.text('REPLACEMENT ' + ('ON' if on_p > 0.5 else 'OFF'), 910, y + 50, 15, 'ice' if on_p > 0.5 else (140, 145, 150), 'mono', 'center')
        if on_p > 0.02:
            f.glow(1030, y + 31, 18, ICE, on_p)
    if together_a > 0:
        f.line([(1060, 140), (1075, 140), (1075, 360), (1060, 360)], (255, 179, 100, int(220 * together_a)), 2)
        f.text('ALL THREE AT ONCE', 1090, 255, 16, 'amber', 'mono', alpha=together_a)
    if warm_a > 0:
        f.text('THESE DEVICES HELP KEEP THE SPACECRAFT WARM', 470, 440, 17, 'paper', 'mono', alpha=warm_a)
    if less_a > 0:
        f.pill('LESS POWER USED', 470, 500, 'ice', 20)
    if y27_a > 0:
        f.group(y27_a)
        f.rect(470, 528, 700, 70, (20, 12, 10, 230), (255, 179, 100, 110), 1)
        f.text('WITHOUT IT: ANOTHER SCIENCE INSTRUMENT', 490, 557, 18, 'paper', 'mono')
        f.text('MIGHT HAVE BEEN TURNED OFF AS EARLY AS SUMMER 2027', 490, 584, 16, 'amber', 'mono')
        f.end()
    f.footer('SCHEMATIC  /  SIMPLIFIED  ·  BACKGROUND: ARTIST CONCEPT', 'NASA / JPL-CALTECH')


# ------------------------------------------------------------------ 7. history
def trajectory(f, t, ts, label_a=1.0):
    v = Video(A('trajectory_12s.mp4'))
    f.image(None, 0, 0, 1280, 720, 1.12, 0.5, 0.3, frame=v.at(ts))
    f.shade([(0, '#0a0605c0'), (0.2, '#0a060500')], 0, 0, 0, 720)
    f.kick('VOYAGER 1 TRAJECTORY  /  LAUNCHED 1977', 470, 65)
    f.footer('DATA VISUALIZATION', 'NASA SCIENTIFIC VISUALIZATION STUDIO')


def jupiter(f, t, ts):
    v = Video(A('jupiter_clouds.mp4'))
    fr = v.at(ts).crop((0, 112, 1620, 698))
    f.image(None, 0, 0, 1280, 720, 1.0 + 0.04 * smooth(ts / 3.7), 0.5, 0.5, frame=fr)
    f.shade([(0, '#00000000'), (0.7, '#00000000'), (1, '#000000aa')], 0, 0, 0, 720)
    f.shade([(0, '#0a0605d0'), (0.18, '#0a060500')], 0, 0, 0, 720)
    f.kick('JUPITER  /  SEQUENCE FROM VOYAGER 1 IMAGES', 470, 65)
    f.footer('NASA PHOTOS SEQUENCE', 'NASA SVS  /  TOM BRIDGMAN')


PB_EARTH = (1307, 1131)            # Earth in paleblue.jpg (px)


def paleblue(f, t, z, ring_a, cap_a):
    """Pale Blue Dot, framed so the dot sits right of centre, then a careful highlight."""
    zoom = 1.0 + 0.6 * z
    fx, fy = 0.62, 0.52
    f.image(A('paleblue.jpg'), 0, 0, 1280, 720, zoom, fx, fy)
    # where the dot lands on screen (design coords)
    iw, ih = 2200, 2177
    sw = min(iw, ih * 1280 / 720) / zoom
    sh = sw * 720 / 1280
    x0, y0 = (iw - sw) * fx, (ih - sh) * fy
    ex = (PB_EARTH[0] - x0) / sw * 1280
    ey = (PB_EARTH[1] - y0) / sh * 720
    if ring_a > 0:
        f.circle(ex, ey, 22, None, (164, 232, 255), 2, alpha=ring_a)
        f.line([(ex + 22, ey - 10), (ex + 80, ey - 50)], (239, 226, 196, int(200 * ring_a)), 2)
        f.text('EARTH', ex + 86, ey - 54, 18, 'ice', 'mono', alpha=ring_a)
    if cap_a > 0:
        f.pill('VOYAGER 1 PHOTO · 1990', 470, 110, 'paper', 18)
    f.footer('ARCHIVE PHOTO  /  PALE BLUE DOT REVISITED', 'NASA / JPL-CALTECH')
    return ex, ey


def heliopause(f, t, cross_p, label_a, inter_a):
    f.background('#1f1713', '#0a0706')
    f.starfield(t * 0.4)
    f.kick('THE HELIOSPHERE  /  2012', 470, 65)
    cx, cy = 820, 330
    # bubble shaped by the solar wind (teardrop toward the tail)
    pts = []
    for k in range(73):
        a = math.radians(k * 5)
        r = 190 * (1 + 0.35 * max(0, -math.cos(a)) ** 1.5)
        pts.append((cx + r * math.cos(a) * 1.15, cy + r * math.sin(a) * 0.82))
    f.poly(pts, (120, 40, 25, 70))
    f.line(pts, (239, 226, 196, 150), 2)
    f.glow(cx, cy, 40, (255, 210, 120))
    f.circle(cx, cy, 8, (255, 222, 150))
    f.text('SUN', cx, cy + 34, 15, 'paper', 'mono', 'center')
    # Voyager path crossing the boundary (up-right)
    a = math.radians(-28)
    r_edge = 190 * 1.15
    p = lerp(0.35, 1.35, cross_p)
    vx, vy = cx + r_edge * p * math.cos(a), cy + r_edge * 0.82 / 1.15 * p * math.sin(a) * 1.15
    f.line([(cx + 30 * math.cos(a), cy + 30 * math.sin(a)), (vx, vy)], (255, 179, 100, 200), 2, dash=(6, 7))
    f.circle(vx, vy, 6, 'amber')
    f.text('VOYAGER 1', vx + 12, vy - 10, 15, 'amber', 'mono')
    if label_a > 0:
        f.text('HELIOPAUSE', 1010, 140, 20, 'ice', 'mono', alpha=label_a)
        f.text('EDGE OF THE SOLAR-WIND BUBBLE', 1010, 162, 13, 'paper', 'mono_r', alpha=label_a)
    if inter_a > 0:
        f.text('INTERSTELLAR SPACE', 1050, 470, 24, 'ice', 'sans', alpha=inter_a)
    f.footer('SCHEMATIC  /  NOT TO SCALE')


def finale(f, t, hours, pulse_back, text_a):
    """Return to the cover composition: hour 0 / 24 / 48 marks, reply pulse reaches Earth."""
    cover(f, t, pulse=1.0 - pulse_back, text_a=0.0, zoom=0.3)
    xs = [73, 621, 1170]
    lab = ['HOUR 0', 'HOUR 24', 'HOUR 48']
    sub = ['SIGNAL LEAVES EARTH', 'VOYAGER HEARS IT', 'EARTH HEARS BACK']
    for k in range(3):
        a = hours[k]
        if a <= 0:
            continue
        x = [130, 621, 1100][k]
        f.circle(xs[k] if k != 1 else 621, 554, 6, 'amber' if k == 2 else 'ice', alpha=a)
        f.text(lab[k], x, 520, 22, 'amber' if k == 2 else 'ice', 'sans', 'center', alpha=a)
        f.text(sub[k], x, 600, 13, 'paper', 'mono', 'center', alpha=a)
    if text_a > 0:
        f.text('STILL SOMETHING ON THE OTHER END OF THE LINE', 621, 470, 20, 'paper', 'mono', 'center', alpha=text_a)


# ------------------------------------------------------------------ poster texture
_GRAIN = None


def retro(img, amount=0.55):
    """Add the cover's paper/print grain so diagrams sit in the same poster world."""
    global _GRAIN
    import numpy as np
    from PIL import Image, ImageFilter
    if _GRAIN is None:
        pl = Image.open('/mnt/project-files/voyager/EP013/cover/layers/plate.png').convert('L')
        a = np.asarray(pl, np.float32)
        _GRAIN = a - np.asarray(pl.filter(ImageFilter.GaussianBlur(3)), np.float32)
        _GRAIN[0:170, 1480:1920] = _GRAIN[300:470, 1000:1440]      # no corner label in the grain
    arr = np.asarray(img, np.float32) + _GRAIN[..., None] * amount
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
