"""Text recorder for MOBILE_READABILITY_QA: when active, every string drawn by kinetic.draw_text, text.plate or typeset.put is logged
with its font size (px at the render size), screen box, colour, alpha and the overlay class that drew it. Inactive (None) by default:
rendering is unchanged and costs nothing."""
STATE = {"rec": None, "tag": None}


def note(s, px, box, color, alpha):
    rec = STATE["rec"]
    if rec is None or box is None or alpha < 0.5 or not str(s).strip(): return
    rec.append(dict(text=str(s), px=float(px), box=tuple(float(v) for v in box), color=tuple(int(c) for c in color[:3]), alpha=float(alpha), tag=STATE["tag"]))
