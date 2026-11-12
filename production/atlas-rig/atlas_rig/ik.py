"""Two-bone IK with a fixed bend side and a predictable reach limit."""
import math
import numpy as np

REACH_MAX = 0.998   # never straighten a limb fully (avoids the knee/elbow snapping)
SOFT = 0.018        # soft-limit band, as a fraction of the full chain length


def two_bone(root, target, L1, L2, bend, soft=True):
    """Return (mid_joint, end, info).

    bend: +1 / -1 picks the side of the root->target line the mid joint lies on
    (fixed per limb, so an elbow or knee can never flip to the other side).
    Out-of-range targets: the end stops on the line root->target at the reach limit
    (outer limit eased in over the last SOFT of the range) - no stretching, no flips.
    info: reached (bool), err (px from target), clamp ('', 'far', 'near').
    """
    root = np.asarray(root, float)
    target = np.asarray(target, float)
    d = target - root
    dist = math.hypot(d[0], d[1])
    dirn = d / dist if dist > 1e-9 else np.array([0.0, 1.0])
    hi = (L1 + L2) * REACH_MAX
    lo = abs(L1 - L2) + 1e-3
    clamp = ''
    dc = dist
    if soft:
        band = SOFT * (L1 + L2)
        start = hi - band
        if dist > start:
            dc = start + band * (1 - math.exp(-(dist - start) / band))
    if dc > hi:
        dc = hi
    if dist > hi:
        clamp = 'far'
    if dc < lo:
        dc = lo
        clamp = 'near'
    cosA = (L1 * L1 + dc * dc - L2 * L2) / (2 * L1 * dc)
    A = math.acos(max(-1.0, min(1.0, cosA)))
    base = math.atan2(dirn[1], dirn[0])
    a = base + bend * A
    mid = root + L1 * np.array([math.cos(a), math.sin(a)])
    end = root + dirn * dc
    err = float(math.hypot(*(end - target)))
    return mid, end, {'reached': err < 0.5, 'err': err, 'clamp': clamp}


def bend_side(root, mid, end):
    """Sign of the bend (z of cross(root->end, root->mid)): +1 / -1."""
    a = np.subtract(end, root)
    b = np.subtract(mid, root)
    return 1 if a[0] * b[1] - a[1] * b[0] > 0 else -1


def max_reach(L1, L2):
    """Distance at which a target is still met exactly (below the soft band)."""
    return (L1 + L2) * (REACH_MAX - SOFT)
