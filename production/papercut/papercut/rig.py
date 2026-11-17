"""Articulated paper-cut ATLAS built from the owner's parts sheet (assets/parts_v1, 2026-11-17).

Cut-out puppet rules:
- every part is a 1:1 cut from the sheet, uniformly scaled by ONE factor for the whole body
  (no per-part or non-uniform stretching, proportions never change between frames);
- joints rotate about the centre of the round end that tucks under/over the neighbour part, so the
  overlap always hides the seam (no gaps when a joint bends);
- face changes happen inside the one head (eye patch), never by swapping heads.

    rig = Rig(height_px=430)
    pose = Pose()                      # all angles in degrees, + = clockwise on screen
    pose.arm_B = (-95, -20, 70)        # shoulder, elbow, wrist
    rig.render(frame, pose, feet=(300, 960))
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field, replace
from pathlib import Path

import numpy as np
from PIL import Image

PARTS_DIR = Path(__file__).resolve().parent.parent / "assets" / "parts_v1"


class RigError(RuntimeError):
    pass


def _mat(tx=0.0, ty=0.0, deg=0.0, s=1.0):
    c, n = math.cos(math.radians(deg)) * s, math.sin(math.radians(deg)) * s
    return np.array([[c, -n, tx], [n, c, ty], [0, 0, 1]], float)


def T(x, y):
    return _mat(x, y)


def R(deg):
    return _mat(0, 0, deg)


@dataclass
class Pose:
    lean: float = 0.0                  # torso about the pelvis
    head: float = 0.0                  # head about the neck (on top of the lean)
    arm_A: tuple = (0.0, 0.0, 0.0)     # viewer-left arm: shoulder, elbow, wrist
    arm_B: tuple = (0.0, 0.0, 0.0)     # viewer-right arm
    leg_A: tuple = (0.0, 0.0, None)    # hip, knee, ankle (None = ankle keeps the boot flat on the ground)
    leg_B: tuple = (0.0, 0.0, None)
    hand_B: str = "fist_B"             # glove drawing on arm B: fist_B | point_B | open_B
    hand_A: str = "fist_A"
    eyes: str = "open"                 # open | half | closed
    scarf: float = 0.0                 # extra scarf swing (lag), degrees

    def mix(self, other: "Pose", u: float) -> "Pose":
        lerp = lambda a, b: None if a is None or b is None else a + (b - a) * u
        tl = lambda a, b: tuple(lerp(x, y) for x, y in zip(a, b))
        return replace(self, lean=lerp(self.lean, other.lean), head=lerp(self.head, other.head),
                       arm_A=tl(self.arm_A, other.arm_A), arm_B=tl(self.arm_B, other.arm_B),
                       leg_A=tl(self.leg_A, other.leg_A), leg_B=tl(self.leg_B, other.leg_B))


# ---------------------------------------------------------------- skeleton (sheet pixel units)
# Each joint: (part, parent, attach point in parent px, pivot in part px, z-order)
# Pivots are the centres of the round ends; the numbers come from the peg detection in parts.json and
# were checked against the assembled reference figure (see scenes/rig_sheet.py).
TORSO_PELVIS = (126.0, 228.0)
SKELETON = {
    "torso":   (None,     None,            TORSO_PELVIS,   50),
    "head":    ("torso",  (128.0, 34.0),   (196.0, 320.0), 90),
    "scarf":   ("torso",  (126.0, 50.0),   (196.0, 36.0),  80),
    "uarm_A":  ("torso",  (50.0, 90.0),   (61.9, 88.6),   30),
    "farm_A":  ("uarm_A", (34.5, 178.0),   (47.4, 95.7),   60),
    "hand_A":  ("farm_A", (36.7, 164.9),   None,           70),
    "uarm_B":  ("torso",  (206.0, 86.0),   (48.2, 89.7),   31),
    "farm_B":  ("uarm_B", (69.5, 178.0),   (38.5, 95.0),   61),
    "hand_B":  ("farm_B", (50.5, 163.9),   None,           71),
    "thigh_A": ("torso",  (84.0, 168.0),   (67.5, 70.0),   20),
    "shin_A":  ("thigh_A", (39.5, 150.0),  (45.0, 66.0),   12),
    "boot_A":  ("shin_A", (44.5, 172.0),   (96.0, 44.0),   10),
    "thigh_B": ("torso",  (170.0, 168.0),  (38.0, 68.0),   21),
    "shin_B":  ("thigh_B", (64.5, 146.0),  (40.5, 66.0),   13),
    "boot_B":  ("shin_B", (42.0, 170.0),   (55.0, 43.0),   11),
}
HAND_PIVOT_DROP = 20.0      # glove pivot = its (removed) tab centre + this, i.e. just inside the glove top


def _load(name):
    meta = json.loads((PARTS_DIR / "parts.json").read_text())
    p = PARTS_DIR / f"{name}.png"
    want = meta["parts"][name]["sha256"]
    if hashlib.sha256(p.read_bytes()).hexdigest() != want:
        raise RigError(f"part {name} does not match parts.json checksum")
    return Image.open(p).convert("RGBA"), meta["parts"][name]


class Rig:
    BODY = ["torso", "head", "scarf", "uarm_A", "farm_A", "uarm_B", "farm_B", "thigh_A", "shin_A", "boot_A",
            "thigh_B", "shin_B", "boot_B"]
    HANDS = ["fist_A", "fist_B", "point_B", "point_back", "open_A", "open_B"]

    def __init__(self, height_px: float = 430.0, ss: int = 1):
        self.meta = {}
        src = {}
        for n in self.BODY + self.HANDS + ["face_closed", "reference"]:
            src[n], self.meta[n] = _load(n)
        # one uniform scale for the whole puppet: the reference figure (608 px on the sheet) -> height_px
        self.k = height_px / 608.0 * 0.87
        self.ss = ss
        k = self.k * ss
        self.img = {}
        for n, im in src.items():
            w, h = max(1, round(im.width * k)), max(1, round(im.height * k))
            self.img[n] = im.resize((w, h), Image.Resampling.LANCZOS)
        self.kx = {n: (self.img[n].width / src[n].width, self.img[n].height / src[n].height) for n in src}
        self._heads = {"open": self.img["head"]}
        self._build_eyes(src)

    # ------------------------------------------------------------ face (inside the one head)
    # Eye centres on the helmet head and on the closed-eye head, measured on the sheet parts.
    HEAD_EYES = ((173.8, 228.6), (249.6, 217.6))
    CLOSED_EYES = ((88.2, 116.3), (158.0, 102.4))

    def _build_eyes(self, src):
        """Closed eyes: the drawn closed-eye strokes from the sheet's closed-eye head, placed by the eye
        centres onto the helmet head (similarity transform), feathered skin patch. Half: open eye squashed."""
        head = src["head"]
        fc = src["face_closed"]
        (a1, a2), (b1, b2) = self.HEAD_EYES, self.CLOSED_EYES
        va, vb = np.subtract(a2, a1), np.subtract(b2, b1)
        sc = np.hypot(*va) / np.hypot(*vb)
        rot = math.degrees(math.atan2(va[1], va[0]) - math.atan2(vb[1], vb[0]))
        closed = head.copy()
        for (hx, hy), (cx, cy) in zip(self.HEAD_EYES, self.CLOSED_EYES):
            pw, ph = 27, 29                       # patch half size in closed-face px (keeps the donor blush out)
            patch = fc.crop((int(cx - pw), int(cy - ph), int(cx + pw), int(cy + ph)))
            patch = patch.resize((round(patch.width * sc), round(patch.height * sc)), Image.Resampling.LANCZOS)
            patch = patch.rotate(-rot, resample=Image.Resampling.BICUBIC)
            yy, xx = np.mgrid[0:patch.height, 0:patch.width]
            ex, ey = patch.width / 2, patch.height / 2
            d = np.hypot((xx - ex) / (ex * 0.95), (yy - ey) / (ey * 0.95))
            fe = np.clip((1.0 - d) / 0.25, 0, 1)
            a = (np.asarray(patch.getchannel("A"), np.float32) * fe).astype(np.uint8)
            patch.putalpha(Image.fromarray(a))
            closed.alpha_composite(patch, (int(round(hx - patch.width / 2)), int(round(hy - patch.height / 2))))
        self._closed_src = closed
        k = self.k * self.ss
        self._heads["closed"] = closed.resize(self.img["head"].size, Image.Resampling.LANCZOS)
        half = head.copy()
        for (hx, hy) in self.HEAD_EYES:
            box = (int(hx - 16), int(hy - 26), int(hx + 16), int(hy + 26))
            eye = head.crop(box)
            skin = closed.crop(box)
            half.alpha_composite(skin, box[:2])
            sq = eye.resize((eye.width, eye.height // 2), Image.Resampling.LANCZOS)
            half.alpha_composite(sq, (box[0], int(hy - sq.height / 2 + 6)))
        self._heads["half"] = half.resize(self.img["head"].size, Image.Resampling.LANCZOS)

    # ------------------------------------------------------------ kinematics
    def _hand_pivot(self, hand):
        pg = self.meta[hand]["pegs"]["top"]["c"]
        return (pg[0], pg[1] + HAND_PIVOT_DROP)

    def transforms(self, pose: Pose):
        """Part -> canvas matrices in SHEET units, root pelvis at origin."""
        ang = {"torso": pose.lean, "head": pose.head, "scarf": -pose.lean * 0.6 + pose.scarf,
               "uarm_A": pose.arm_A[0], "farm_A": pose.arm_A[1], "hand_A": pose.arm_A[2],
               "uarm_B": pose.arm_B[0], "farm_B": pose.arm_B[1], "hand_B": pose.arm_B[2],
               "thigh_A": pose.leg_A[0], "shin_A": pose.leg_A[1],
               "thigh_B": pose.leg_B[0], "shin_B": pose.leg_B[1]}
        # boots stay level with the ground: ankle = -(world angle of the shin)
        ang["boot_A"] = -(pose.lean + pose.leg_A[0] + pose.leg_A[1]) if pose.leg_A[2] is None else pose.leg_A[2]
        ang["boot_B"] = -(pose.lean + pose.leg_B[0] + pose.leg_B[1]) if pose.leg_B[2] is None else pose.leg_B[2]
        M = {}
        for name, (parent, attach, pivot, _z) in SKELETON.items():
            if name.startswith("hand_"):
                pivot = self._hand_pivot(pose.hand_A if name == "hand_A" else pose.hand_B)
            if parent is None:
                M[name] = R(ang[name]) @ T(-pivot[0], -pivot[1])
            else:
                M[name] = M[parent] @ T(*attach) @ R(ang[name]) @ T(-pivot[0], -pivot[1])
        return M

    def joint_points(self, pose: Pose, feet=(0.0, 0.0)):
        """World (screen) positions of every joint, for QA and for aiming."""
        M, off = self._placed(pose, feet)
        out = {}
        for name, (parent, attach, _p, _z) in SKELETON.items():
            if parent is not None:
                p = M[parent] @ np.array([attach[0], attach[1], 1.0])
                out[name] = (p[0], p[1])
        return out

    def _placed(self, pose, feet):
        M = self.transforms(pose)
        # feet planted: the mean of both boot soles lands on `feet`
        sole = []
        for b in ("boot_A", "boot_B"):
            im = self.meta[b]["size"]
            p = M[b] @ np.array([im[0] / 2, im[1] - 8.0, 1.0])
            sole.append(p[:2])
        c = np.mean(sole, axis=0)
        k = self.k
        S = np.array([[k, 0, feet[0] - c[0] * k], [0, k, feet[1] - c[1] * k], [0, 0, 1.0]])
        return {n: S @ m for n, m in M.items()}, S

    # ------------------------------------------------------------ drawing
    def render(self, frame: Image.Image, pose: Pose, feet=(300.0, 960.0), return_boxes=False):
        """Composite the puppet onto `frame` (RGBA, in place). Returns the bounding box."""
        Mw, _ = self._placed(pose, feet)
        order = sorted(SKELETON, key=lambda n: SKELETON[n][3])
        box = [1e9, 1e9, -1e9, -1e9]
        layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        boxes = {}
        for name in order:
            if name == "head":
                im = self._heads[pose.eyes]
                src_name = "head"
            elif name == "hand_A":
                src_name = pose.hand_A; im = self.img[src_name]
            elif name == "hand_B":
                src_name = pose.hand_B; im = self.img[src_name]
            else:
                src_name = name; im = self.img[name]
            kx, ky = self.kx[src_name]
            # sheet px -> scaled image px
            Sp = np.array([[kx, 0, 0], [0, ky, 0], [0, 0, 1.0]])
            A = Mw[name] @ np.linalg.inv(Sp)          # image px -> screen px
            Ai = np.linalg.inv(A)
            # bounding box on screen
            corners = np.array([[0, 0, 1], [im.width, 0, 1], [0, im.height, 1], [im.width, im.height, 1]], float).T
            sc = A @ corners
            x0, y0 = int(math.floor(sc[0].min())) - 2, int(math.floor(sc[1].min())) - 2
            x1, y1 = int(math.ceil(sc[0].max())) + 2, int(math.ceil(sc[1].max())) + 2
            w, h = x1 - x0, y1 - y0
            # map output (x0+u, y0+v) -> image px
            Ao = Ai @ np.array([[1, 0, x0], [0, 1, y0], [0, 0, 1.0]])
            pm = im.convert("RGBa")
            out = pm.transform((w, h), Image.Transform.AFFINE, tuple(Ao[:2].ravel()), resample=Image.Resampling.BICUBIC)
            layer.alpha_composite(out.convert("RGBA"), (x0, y0)) if x0 >= 0 and y0 >= 0 else _paste_clip(layer, out.convert("RGBA"), x0, y0)
            boxes[name] = (x0, y0, x1, y1)
            box = [min(box[0], x0), min(box[1], y0), max(box[2], x1), max(box[3], y1)]
        frame.alpha_composite(layer)
        return (box, boxes) if return_boxes else box


def _paste_clip(dst, src, x0, y0):
    cx0, cy0 = max(0, -x0), max(0, -y0)
    dst.alpha_composite(src.crop((cx0, cy0, src.width, src.height)), (x0 + cx0, y0 + cy0))
