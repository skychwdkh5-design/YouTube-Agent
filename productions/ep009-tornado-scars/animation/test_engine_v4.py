"""Automated tests for the v4 continuous engine. Run: python3 -m pytest -q test_engine_v4.py  (or python3 test_engine_v4.py)"""
import math
import numpy as np
import engine as E
import motion_qc as Q


def test_hermite_c0_c1_through_keys():
    h = E.Hermite([(0, 0.0), (1, 1.0), (2, 3.0), (3, 3.5)])
    e = 1e-6
    for t in (1.0, 2.0):                                  # position AND velocity continuous through interior keys
        assert abs(h(t - e) - h(t + e)) < 1e-4
        assert abs((h(t) - h(t - e)) / e - (h(t + e) - h(t)) / e) < 1e-2
    assert abs((h(e) - h(0)) / e) < 1e-3                  # ends at rest
    xs = [h(t) for t in np.linspace(0, 3, 301)]
    assert all(b >= a - 1e-9 for a, b in zip(xs, xs[1:]))  # monotone input -> no overshoot


def test_camera_has_no_dead_stop_at_flow_through_keys():
    c = E.Cam([(0, (0, 0, 1.0)), (1, (100, 0, 1.0)), (2, (200, 0, 1.0))])
    assert abs(c(1.0 + 1e-3)[0] - c(1.0 - 1e-3)[0]) / 2e-3 > 50   # still moving at the middle key


def test_turb_has_no_lattice_dwell():
    ts = np.arange(0, 20, 1 / 960); f = np.array([E.turb(t, 3, 1.1) for t in ts]); v = np.abs(np.gradient(f, 1 / 960))
    assert (v < 0.08 * np.median(v)).mean() < 0.06       # value noise (v3) dwells at every node; this must not


def test_gust_pulse_is_c1_at_onset_and_peak():
    e = 1e-5
    assert abs(E.gust_pulse(10 + e, 10, 1.0, 0.4)) < 1e-6
    assert abs((E.gust_pulse(10.4 + e, 10, 1.0, 0.4) - E.gust_pulse(10.4 - e, 10, 1.0, 0.4)) / (2 * e)) < 1e-2   # smooth peak


def test_subpixel_motion_never_freezes():
    """A sprite moved 0.25 px per step must change the frame EVERY step (v3's int() placement froze 3 of 4)."""
    spr = E.Sprite(__import__("PIL.Image", fromlist=["Image"]).new("RGBA", (40, 40), (255, 255, 255, 255)))
    prev = None; same = 0
    for i in range(40):
        c = np.zeros((E.H, E.W, 3), np.float32); E.draw(c, spr, E.mat(300 + 0.25 * i, 300, 0, 1, 1, 20, 20))
        if prev is not None and np.abs(c - prev).max() < 1e-5: same += 1
        prev = c
    assert same == 0
    # centre of mass moves linearly (sub-pixel exact)
    xs = []
    for i in range(0, 40, 4):
        c = np.zeros((E.H, E.W, 3), np.float32); E.draw(c, spr, E.mat(300 + 0.25 * i, 300, 0, 1, 1, 20, 20))
        m = c[..., 0]; xs.append((m.sum(0) * np.arange(E.W)).sum() / m.sum())
    assert np.max(np.abs(np.diff(xs) - 1.0)) < 0.02


def test_remap_matches_affine_for_identity_deformation():
    from PIL import Image
    im = Image.fromarray((np.random.default_rng(1).random((60, 60, 4)) * 255).astype(np.uint8)); spr = E.Sprite(im)
    a = np.zeros((E.H, E.W, 3), np.float32); b = a.copy()
    E.draw(a, spr, E.mat(500, 400, 0, 1, 1, 30, 30), flags=1)
    E.draw_remap(b, spr, lambda X, Y: (X - 500 + 30, Y - 400 + 30), (440, 340, 560, 460))
    assert np.abs(a - b).max() < 0.02


def test_subframe_n1_is_exact_and_blur_conserves_energy():
    f = lambda t: np.full((4, 4, 3), math.sin(t), np.float32)
    assert np.allclose(E.render_frame(f, 1.0, 1), f(1.0))
    ts, ws = E.subtimes(1.0, 4, 0.5); assert abs(sum(ws) - 1) < 1e-9 and abs(np.mean(ts) - 1.0) < 1e-9 and abs(ts[-1] - ts[0] - 0.5 / E.FPS * 0.75) < 1e-9


def test_doc_sampler_is_float_and_continuous():
    from PIL import Image
    im = Image.fromarray((np.random.default_rng(2).random((900, 1200, 3)) * 255).astype(np.uint8)); d = E.Doc(im)
    a = d.render(600, 450, 800.0); b = d.render(600.2, 450, 800.0); c = d.render(600.4, 450, 800.0)
    assert 0 < np.abs(a - b).mean() < np.abs(a - c).mean()


def test_probe_analysis_flags_real_defects_only():
    ok = lambda t: {"o": {"x": 100 * math.sin(t)}}
    assert not any(v["c0_jumps"] or v["c1_resets"] for v in Q.probe_analysis(ok, 0, 6).values())
    jump = lambda t: {"o": {"x": 100 * math.sin(t) + (40 if t > 3 else 0)}}
    assert any(v["c0_jumps"] for v in Q.probe_analysis(jump, 0, 6).values())
    reset = lambda t: {"o": {"x": 50 * t if t < 3 else 150 - 50 * (t - 3)}}
    assert any(v["c1_resets"] for v in Q.probe_analysis(reset, 0, 6).values())
    assert not any(v["c1_resets"] for v in Q.probe_analysis(reset, 0, 6, impacts=[3.0]).values())   # declared impact is allowed


def test_stepping_detector_separates_smooth_from_stepped():
    n = 120; smooth = np.stack([np.full(n, 0.7), np.zeros(n)], 1)
    stepped = np.stack([np.where(np.arange(n) % 4 == 0, 2.8, 0.0), np.zeros(n)], 1)        # 0.7 px/frame average but moves in jumps
    a, b = Q.stepping_report(smooth), Q.stepping_report(stepped)
    assert a["freeze_jump_frames"] == 0 and a["residual_over_speed"] < 0.05
    assert b["freeze_jump_frames"] > 20 and b["residual_over_speed"] > 0.5


if __name__ == "__main__":
    import sys
    fails = 0
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            try: v(); print("PASS", k)
            except Exception as e: fails += 1; print("FAIL", k, repr(e))
    sys.exit(1 if fails else 0)
