"""Pose solver: body controls + IK targets -> joint positions and bone matrices.

Scenes never rotate part images directly. They describe a Pose (where the pelvis is,
where each ankle and wrist should be, where the head looks) and solve() turns it into
bone transforms with constant segment lengths and fixed bend sides.
"""
import math
from dataclasses import dataclass, field

import numpy as np

from .mathx import T, R, S, about, ap, ang, bone_matrix
from .ik import two_bone, bend_side, max_reach
from .face import HEAD_TL


@dataclass
class Pose:
    root: np.ndarray                       # world offset of the rest frame
    pelvis_off: np.ndarray = field(default_factory=lambda: np.zeros(2))
    pelvis_rot: float = 0.0                # deg
    pelvis_cr: float = 0.0                 # counter-rotation (width change, +-0.03)
    torso_rot: float = 0.0                 # deg, relative to the pelvis (lean)
    torso_cr: float = 0.0
    breath: float = 0.0                    # -1..1
    head_rot: float = 0.0                  # deg
    shoulder_off: dict = field(default_factory=lambda: {'n': np.zeros(2), 'f': np.zeros(2)})
    ankle: dict = field(default_factory=dict)       # 'n'/'f' -> world ankle target
    foot_pitch: dict = field(default_factory=lambda: {'n': 0.0, 'f': 0.0})
    wrist: dict = field(default_factory=dict)       # 'n'/'f' -> world wrist target
    hand_dir: dict = field(default_factory=dict)    # 'n'/'f' -> deg, or None = follow forearm
    hand_pose: dict = field(default_factory=lambda: {'n': 'relaxed_near', 'f': 'relaxed'})
    keep_reach: bool = True                # lower the pelvis rather than miss a foot target


@dataclass
class Solved:
    joints: dict
    bones: dict             # bone -> 3x3 rest->world
    hands: dict             # 'n'/'f' -> (Hand, 3x3 image->world)
    head: np.ndarray        # face image (3x sheet px) -> world
    ik: dict                # limb -> info dict
    bend: dict              # limb -> measured bend side
    lengths: dict           # segment -> measured world length
    pelvis_drop: float


def solve(rig, pose):
    J = rig.J
    root = np.asarray(pose.root, float)
    pelvis_w = J['pelvis'] + root + pose.pelvis_off
    drop = 0.0
    for _ in range(3):
        Mpel = T(*(pelvis_w + [0, drop])) @ R(pose.pelvis_rot) @ S(1 + pose.pelvis_cr, 1) @ T(*-J['pelvis'])
        if not pose.keep_reach:
            break
        need = 0.0
        for s in 'nf':
            if s not in pose.ankle:
                continue
            hip = ap(Mpel, J[f'hip_{s}'])
            a = np.asarray(pose.ankle[s], float)
            Rm = max_reach(rig.lengths[f'thigh_{s}'], rig.lengths[f'shin_{s}'])
            dx = a[0] - hip[0]
            if abs(dx) >= Rm:
                continue
            want_y = a[1] - math.sqrt(Rm * Rm - dx * dx)
            need = max(need, want_y - hip[1])
        if need <= 1e-3:
            break
        drop += need
    waist_w = ap(Mpel, J['waist'])
    Mtor = (T(*waist_w) @ R(pose.pelvis_rot + pose.torso_rot)
            @ S(1 - pose.torso_cr, 1 + 0.006 * pose.breath) @ T(*-J['waist']))
    bones = {'pelvis': Mpel, 'torso': Mtor}
    joints = {'pelvis': ap(Mpel, J['pelvis']), 'waist': waist_w, 'neck': ap(Mtor, J['neck'])}
    ik, bend, lengths = {}, {}, {}

    # legs: hip -> knee -> ankle (IK), foot pitch about the ankle
    for s in 'nf':
        hip = ap(Mpel, J[f'hip_{s}'])
        tgt = np.asarray(pose.ankle.get(s, J[f'ankle_{s}'] + root), float)
        L1, L2 = rig.lengths[f'thigh_{s}'], rig.lengths[f'shin_{s}']
        knee, ankle, info = two_bone(hip, tgt, L1, L2, rig.bend[f'leg_{s}'])
        ik[f'leg_{s}'] = info
        bend[f'leg_{s}'] = bend_side(hip, knee, ankle)
        bones[f'thigh_{s}'] = bone_matrix(J[f'hip_{s}'], J[f'knee_{s}'], hip, knee)
        bones[f'shin_{s}'] = bone_matrix(J[f'knee_{s}'], J[f'ankle_{s}'], knee, ankle)
        bones[f'foot_{s}'] = T(*ankle) @ R(pose.foot_pitch.get(s, 0.0)) @ T(*-J[f'ankle_{s}'])
        joints.update({f'hip_{s}': hip, f'knee_{s}': knee, f'ankle_{s}': ankle})
        lengths[f'thigh_{s}'] = float(np.hypot(*(knee - hip)))
        lengths[f'shin_{s}'] = float(np.hypot(*(ankle - knee)))

    # arms: shoulder -> elbow -> wrist (IK), hand aimed separately
    hands = {}
    for s in 'nf':
        sh_rest = J[f'shoulder_{s}'] + pose.shoulder_off.get(s, np.zeros(2))
        sh = ap(Mtor, sh_rest)
        tgt = np.asarray(pose.wrist.get(s, ap(Mtor, J[f'wrist_{s}'])), float)
        L1, L2 = rig.lengths[f'upper_{s}'], rig.lengths[f'fore_{s}']
        el, wr, info = two_bone(sh, tgt, L1, L2, rig.bend[f'arm_{s}'])
        ik[f'arm_{s}'] = info
        bend[f'arm_{s}'] = bend_side(sh, el, wr)
        bones[f'upper_{s}'] = bone_matrix(J[f'shoulder_{s}'], J[f'elbow_{s}'], sh, el)
        bones[f'fore_{s}'] = bone_matrix(J[f'elbow_{s}'], J[f'wrist_{s}'], el, wr)
        joints.update({f'shoulder_{s}': sh, f'elbow_{s}': el, f'wrist_{s}': wr})
        lengths[f'upper_{s}'] = float(np.hypot(*(el - sh)))
        lengths[f'fore_{s}'] = float(np.hypot(*(wr - el)))
        d = pose.hand_dir.get(s)
        if callable(d):
            d = d(wr, el)
        if d is None:
            d = ang(wr - el) - 4
        h = rig.hands[pose.hand_pose.get(s, 'relaxed')]
        sc = h.length / np.hypot(*(h.tip - h.wrist))
        Mh = T(*wr) @ R(d) @ S(sc) @ R(-ang(h.tip - h.wrist)) @ T(*-h.wrist)
        hands[s] = (h, Mh)

    # head turns about the neck; helmet follows the torso with a damped share of the turn
    hd = rig.head
    Mhead = (Mtor @ about(J['neck'], pose.head_rot) @ T(hd['bubble_c'][0], hd['bubble_c'][1] + hd['dy'])
             @ S(hd['scale']) @ T(*-hd['old_c']) @ T(*HEAD_TL) @ S(1 / 3))
    bones['helmet'] = Mtor @ about(J['neck'], pose.head_rot * 0.25)
    return Solved(joints, bones, hands, Mhead, ik, bend, lengths, drop)
