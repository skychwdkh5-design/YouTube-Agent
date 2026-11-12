"""Artemis II (EP014) scene graphics. Notebook / sepia palette of the approved THEY SAW THIS
cover. NASA materials keep their original labels and colours; anything drawn by us is
labelled SCHEMATIC or CONCEPT ILLUSTRATION. Design space 1280x720 (x1.5 on output)."""
import math
import os

import numpy as np
from PIL import Image, ImageFilter

from engine_path import *            # noqa
from gfx import Frame, PAL, rng, lerp, smooth, clamp, Video
from layers import Stack

SRC = '/mnt/project-files/artemis/EP014/src'
A = lambda n: os.path.join(SRC, 'assets', n)
PAL.update(ice=(247, 226, 190), amber=(240, 122, 30), red=(232, 70, 40), paper=(250, 240, 222))
ORANGE, PAPER, INK = PAL['amber'], PAL['paper'], (34, 26, 20)
STACK = Stack('/mnt/project-files/artemis/EP014/cover/layers')
# cover mark circles (screen px) - drawn illustration, NOT observation positions
MARKS = [(1102, 196), (1390, 312), (905, 505), (1366, 603), (1212, 860)]
MOON_C = (1175, 500)

# moon_notes.jpg (2200x1238): NASA annotated simulation, original pixels (image px)
NOTE = {'jeremy': (1265, 66), 'reid': (1760, 192), 'ike': (1298, 1067), 'purple': (517, 902),
        'm2': (962, 704), 'm4': (1061, 875), 'm1': (1210, 737), 'm3': (1340, 693), 'm5': (1168, 316)}
NOTES_BOX = (380, 92, 842, 474)          # design px: where the NASA document sits (ATLAS left of it)


def cover(t, push=0.0, title_out=0.0, mark_pulse=0.0, focus=2):
    """Cover layers. push 0..1 = camera moves in on MARKS[focus]."""
    fx, fy = MARKS[focus]
    s = 1 + 0.9 * smooth(push)
    cam = (0.0, 0.0, s, fx, fy)
    spec = [('plate', dict(dy=0.0)),
            ('moon', dict(s=1 + 0.004 * t, cx=MOON_C[0], cy=MOON_C[1])),
            ('marks', dict(s=1 + 0.004 * t, cx=MOON_C[0], cy=MOON_C[1], alpha=1.0)),
            ('ship', dict(dx=-2.5 * t, dy=1.2 * math.sin(t * 0.8))),
            ('title', dict(dx=-120 * smooth(title_out), alpha=1 - smooth(title_out)))]
    img = STACK.render(spec, cam=cam)
    if mark_pulse > 0:
        f = Frame(base=img)
        x, y = MARKS[focus]
        x = fx + (x - fx) * s
        y = fy + (y - fy) * s
        k = 0.5 + 0.5 * math.sin(t * 5.0)
        f.circle(x / 1.5, y / 1.5, 34 * s / 1.5 + 6 * k, None, ORANGE, 3, alpha=mark_pulse * (0.4 + 0.6 * k))
        img = f.done()
    return img


def notes_to_screen(p, z=1.0, fx=0.51, fy=0.47):
    """NASA document pixel -> screen px, for the NOTES_BOX framing with zoom z."""
    x, y, w, h = NOTES_BOX
    iw, ih = 2200, 1238
    sw = min(iw, ih * w / h) / z
    sh = sw * h / w
    x0, y0 = (iw - sw) * fx, (ih - sh) * fy
    return ((x + (p[0] - x0) / sw * w) * 1.5, (y + (p[1] - y0) / sh * h) * 1.5)


def notes(f, t, z=1.0, hi=None, hi_a=0.0, big_a=0.0, kick='CREW RECORD  /  ARTEMIS II FLYBY'):
    f.background('#2a2119', '#0d0a08')
    x, y, w, h = NOTES_BOX
    f.rect(x - 4, y - 4, w + 8, h + 8, (10, 8, 7, 255), PAL['ice'] + (60,), 1)
    f.image(A('moon_notes.jpg'), x, y, w, h, z, 0.51, 0.47)
    f.kick(kick, x, 66, 'amber')
    if hi is not None and hi_a > 0:
        sx, sy = notes_to_screen(NOTE[hi], z)
        f.circle(sx / 1.5, sy / 1.5, 44 if hi.startswith('m') else 70, None, PAL['ice'], 2, alpha=hi_a)
    if big_a > 0:
        f.text('46,000', 40, 250, 74, 'paper', 'sans', alpha=big_a)
        f.text('MILES AWAY', 44, 292, 24, 'amber', 'sans', alpha=big_a)
        f.text('≈ 74,000 KM  ·  APPROXIMATE', 44, 322, 14, (228, 219, 217), 'mono', alpha=big_a)
    f.footer('ANNOTATED SIMULATION  ·  ORIGINAL NASA ANNOTATIONS', 'NASA', 'amber')


def geometry(f, t, p, blackout_a, label='WHEN THE MOON BLOCKS THE RADIO PATH'):
    """Orion passes behind the Moon as seen from Earth. p: 0..1 along its arc."""
    f.background('#1d1814', '#090706')
    f.starfield(t * 0.2, 70)
    f.kick(label, 470, 66, 'amber')
    ex, ey, mx, my, R = 330, 300, 860, 300, 230
    a = lerp(-1.1, 1.04, p)
    ox, oy = mx + R * math.cos(a), my + R * math.sin(a)
    blocked = 0.32 < p < 0.78
    f.line([(ex, ey), (ox, oy)], PAL['red'] if blocked else (210, 190, 160), 2, dash=(9, 12))
    f.circle(mx, my, R, None, (200, 180, 150, 70), 1)
    f.circle(mx, my, 118, (40, 36, 38), (190, 180, 175), 2)
    f.circle(mx - 29, my - 21, 80, (52, 48, 50))
    f.circle(mx - 26, my - 40, 40, (46, 42, 44))
    f.glow(ex, ey, 46, (60, 120, 200), 0.6)
    f.circle(ex, ey, 30, (36, 80, 130), (190, 220, 240), 2)
    f.circle(ox, oy, 8, 'paper')
    f.text('EARTH', ex, ey + 62, 18, 'paper', 'mono', 'center')
    f.text('MOON', mx, my + 150, 18, 'paper', 'mono', 'center')
    f.text('ORION', ox + 18, oy - 12, 18, 'paper', 'mono')
    if blackout_a > 0:
        f.text('PLANNED RADIO BLACKOUT', 1220, 600, 36, 'red', 'sans', 'right', alpha=blackout_a)
    f.footer('SCHEMATIC  /  NOT TO SCALE', '', 'amber')


def photo(f, t, z, kick, label, credit, path=None, frame=None, fx=0.5, fy=0.45):
    """Real material in a frame (ATLAS presents it from the left, never stands inside it)."""
    f.background('#2a2119', '#0d0a08')
    x, y, w, h = NOTES_BOX
    f.rect(x - 4, y - 4, w + 8, h + 8, (10, 8, 7, 255), PAL['ice'] + (60,), 1)
    f.image(path, x, y, w, h, z, fx, fy, frame=frame)
    f.kick(kick, x, 66, 'amber')
    f.footer(label, credit, 'amber')


def impact(f, t, rock_p, atm_a, speed_a, flash, flash_a_label):
    """Schematic: a small rock, no thick atmosphere, high-speed hit, brief flash."""
    f.background('#1d1814', '#090706')
    f.starfield(t * 0.3, 60)
    f.kick('PICTURE A SMALL ROCK', 470, 66, 'amber')
    # lunar surface arc
    cx, cy, R = 860, 1180, 640
    pts = [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a))) for a in range(200, 341, 2)]
    f.poly(pts + [(1280, 720), (470, 720)], (58, 52, 50, 255))
    f.line(pts, (200, 190, 180), 2)
    hit = (930, cy - R + 8)
    sx, sy = 1240, 120
    px, py = lerp(sx, hit[0], rock_p), lerp(sy, hit[1], rock_p)
    if rock_p < 1:
        f.line([(lerp(sx, hit[0], max(0, rock_p - 0.25)), lerp(sy, hit[1], max(0, rock_p - 0.25))), (px, py)], (240, 200, 150, 160), 3)
        f.circle(px, py, 7, (180, 160, 140), (240, 220, 200), 1)
    if atm_a > 0:
        f.text('NO THICK ATMOSPHERE TO SLOW IT', 490, 180, 20, 'paper', 'mono', alpha=atm_a)
    if speed_a > 0:
        f.text('HIGH SPEED', 490, 214, 20, 'amber', 'mono', alpha=speed_a)
    if flash > 0:
        f.glow(hit[0], hit[1] - 4, 70 * flash + 10, (255, 240, 200), flash)
        f.circle(hit[0], hit[1] - 4, 6 * flash + 1, (255, 252, 240), alpha=flash)
    if flash_a_label > 0:
        f.text('A BRIEF FLASH OF LIGHT', 990, 460, 24, 'paper', 'sans', alpha=flash_a_label)
    f.footer('SCHEMATIC  /  NOT TO SCALE', '', 'amber')


def pinprick(f, t, a):
    """Schematic: how small a flash looks from Orion (a dot on a dark disc)."""
    f.background('#100c0a', '#050404')
    f.starfield(t * 0.2, 90)
    f.kick('FROM ORION', 470, 66, 'amber')
    f.circle(860, 360, 230, (24, 22, 22), (90, 86, 84), 1)
    k = 0.5 + 0.5 * math.sin(t * 9)
    if a > 0:
        f.glow(800, 300, 14, (255, 245, 220), a * k)
        f.circle(800, 300, 1.6, (255, 250, 240), alpha=a * (0.5 + 0.5 * k))
        f.text('A PINPRICK', 1110, 560, 30, 'paper', 'sans', 'center', alpha=a)
    f.footer('SCHEMATIC  /  SIZE EXAGGERATED FOR VISIBILITY', '', 'amber')


def views(f, t, a_img, a_notes, a_sum, cam_a=0.0):
    """Two records: the crew's images and the crew's notes -> what they reported."""
    f.background('#2a2119', '#0d0a08')
    f.kick('TWO DIFFERENT RECORDS', 470, 66, 'amber')
    if cam_a > 0:
        f.text('SEEING A FLASH  ≠  CAPTURING IT ON CAMERA', 470, 118, 22, 'paper', 'sans', alpha=cam_a)
    if a_img > 0:
        f.rect(468, 158, 344, 230, None, PAL['ice'] + (90,), 1, alpha=a_img)
        f.image(A('eclipse.jpg'), 470, 160, 340, 226, 1.25, 0.5, 0.42, alpha=a_img)
        f.text('IMAGES: THE CREW’S VIEW', 470, 412, 17, 'paper', 'mono', alpha=a_img)
    if a_notes > 0:
        f.rect(868, 158, 344, 196, None, PAL['ice'] + (90,), 1, alpha=a_notes)
        f.image(A('moon_notes.jpg'), 870, 160, 340, 192, 1.0, 0.5, 0.5, alpha=a_notes)
        f.text('NOTES: WHERE THEY SAW LIGHT', 870, 412, 17, 'paper', 'mono', alpha=a_notes)
    if a_sum > 0:
        f.rect(470, 450, 742, 70, (40, 26, 16, 220), ORANGE + (140,), 1, alpha=a_sum)
        f.text('TOGETHER: A RECONSTRUCTION OF WHAT THEY REPORTED', 490, 494, 21, 'amber', 'sans', alpha=a_sum)
    f.footer('ARCHIVE PHOTO + ANNOTATED SIMULATION', 'NASA', 'amber')


# ------------------------------------------------------------------ texture
_GRAIN = None


def retro(img, amount=0.4):
    global _GRAIN
    if _GRAIN is None:
        pl = Image.open('/mnt/project-files/artemis/EP014/cover/layers/plate.png').convert('L').crop((1640, 680, 1800, 780))
        a = np.asarray(pl, np.float32)
        hp = a - np.asarray(pl.filter(ImageFilter.GaussianBlur(3)), np.float32)
        row = np.concatenate([hp, hp[:, ::-1]] * 6, 1)[:, :1920]
        _GRAIN = np.concatenate([row, row[::-1]] * 6, 0)[:1080]
    arr = np.asarray(img, np.float32) + _GRAIN[..., None] * amount
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
