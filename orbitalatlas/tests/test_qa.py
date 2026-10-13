import unittest
import numpy as np
from orbitalatlas import qa as Q, layers as L, camera as C, synthetic as S, transitions as TR, sequence as SQ

SZ = (160, 90)
CFG = Q.QAConfig(size=SZ, fps=30.0)


def textured(seed, level=100):
    """smooth texture (like real imagery: neighbouring pixels correlate), so a 2 px pan changes little."""
    from PIL import Image
    rng = np.random.default_rng(seed); small = np.clip(level + rng.normal(0, 40, (9, 16, 3)), 0, 255).astype(np.uint8)
    return np.asarray(Image.fromarray(small).resize(SZ, Image.BICUBIC))


def drift(n, seed=1, step=2):
    """slowly panning texture: realistic small diffs."""
    base = textured(seed); return [np.roll(base, i * step, axis=1) for i in range(n)]


def issues(frames, **kw):
    return Q.check_stats(Q.analyse(frames, CFG), CFG, **kw)


class TestVideoChecks(unittest.TestCase):
    def test_clean_pan_has_no_issues(self): self.assertEqual(issues(drift(120)), [])
    def test_black_frames_flagged_but_declared_fade_allowed(self):
        f = drift(60); f[20:26] = [np.zeros_like(f[0])] * 6
        self.assertIn("black_frames", [i["check"] for i in issues(f)])
        self.assertNotIn("black_frames", [i["check"] for i in issues(f, allowed_dark=[(0.6, 0.9)], cuts=[20 / 30, 26 / 30])])
    def test_one_or_two_black_frames_are_not_flagged(self):
        f = drift(60); f[20] = np.zeros_like(f[0]); self.assertNotIn("black_frames", [i["check"] for i in issues(f, cuts=[20 / 30, 21 / 30])])
    def test_blank_fill_region_flagged(self):
        f = drift(60)
        for i in range(10, 30): f[i] = f[i].copy(); f[i][:, :80] = (11, 15, 20)       # half the frame uncovered, ink fill
        self.assertIn("blank_region", [i["check"] for i in issues(f, cuts=[10 / 30, 30 / 30])])
    def test_dark_but_textured_scene_is_not_blank_or_black(self):
        f = [np.clip(textured(i, 20) * 0.5, 0, 255).astype(np.uint8) for i in range(1)] * 1
        f = [np.roll(f[0], i, axis=1) for i in range(60)]; r = [i["check"] for i in issues(f)]
        self.assertNotIn("blank_region", r)
    def test_hard_cut_is_a_discontinuity_unless_declared(self):
        f = drift(30, 1) + [np.roll(textured(2, 190), i * 2, axis=1) for i in range(30)]    # a cut to a much brighter shot; low-contrast cuts stay under jump_floor (documented limitation)
        self.assertIn("discontinuity", [i["check"] for i in issues(f)]); self.assertEqual([i for i in issues(f, cuts=[1.0]) if i["check"] == "discontinuity"], [])
    def test_freeze_flagged_but_hold_declared_passes_and_short_hold_ok(self):
        f = drift(30) + [drift(30)[-1]] * 150
        self.assertIn("static_sequence", [i["check"] for i in issues(f)])
        self.assertNotIn("static_sequence", [i["check"] for i in issues(f, holds=[(1.0, 6.0)])])
        g = drift(30) + [drift(30)[-1]] * 60; self.assertNotIn("static_sequence", [i["check"] for i in issues(g)])      # 2 s still shot is legitimate
    def test_transition_without_motion_flagged(self):
        f = drift(30) + [drift(30)[-1]] * 30 + drift(30, 3)
        tr = [dict(index=0, kind="push", t0=1.0, t1=2.0, declared=1.0, ease="x")]
        self.assertIn("transition_no_motion", [i["check"] for i in issues(f, transitions=tr, holds=[(1, 2)])])


class TestScheduleAndAssets(unittest.TestCase):
    def test_duration_checks(self):
        sched = dict(duration=10, shots=[], transitions=[dict(index=0, kind="push", t0=1, t1=1.1, declared=0.1, ease="x"), dict(index=1, kind="dissolve", t0=3, t1=4.0, declared=0.5, ease="x")])
        r = [i["detail"] for i in Q.check_schedule(sched, CFG)]; self.assertEqual(len(r), 2)
    def test_repetition_flagged(self):
        t = lambda k, i: dict(index=i, kind=k, t0=i, t1=i + 0.5, declared=0.5, ease="x")
        self.assertTrue([i for i in Q.check_schedule(dict(duration=9, shots=[], transitions=[t("push", 0), t("push", 1), t("push", 2)]), CFG) if i["check"] == "repetitive_transitions"])
    def test_missing_asset(self): self.assertEqual(Q.check_assets(["/no/such/file.png"])[0]["check"], "missing_asset"); self.assertFalse(Q.run_video("/no/file.mp4")["ok"])


class TestCameraAndOverlayChecks(unittest.TestCase):
    def setUp(self): self.img, _ = S.islands((1200, 675), 3)
    def test_invalid_crop_and_magnification_flagged(self):
        sc = L.Scene(self.img, [dict(t=0, center=(30, 30), height=600), dict(t=1, center=(30, 30), height=60)], size=(320, 180), clamp=False)
        r = [i["check"] for i in Q.check_camera(sc, Q.QAConfig(max_magnification=1.5))]; self.assertIn("camera_window_outside_image", r); self.assertIn("camera_over_magnified", r)
    def test_good_camera_passes(self):
        sc = L.Scene(self.img, [dict(t=0, center=(600, 337), height=600), dict(t=2, center=(700, 337), height=400)], size=(320, 180)); self.assertEqual(Q.check_camera(sc), [])
    def test_anchor_must_stay_in_safe_frame(self):
        sc = L.Scene(self.img, [dict(t=0, center=(300, 300), height=300)], size=(320, 180), anchors={"far": (1000, 600)})
        self.assertTrue(Q.check_camera(sc, must_show={"far": (0, 0.5)}))
    def test_out_of_frame_text_and_collision_flagged(self):
        ov = [L.ScreenText((0.9, 0.5), "TOO FAR RIGHT", 0.12, 0.0, group="a"), L.ScreenText((0.1, 0.1), "OVERLAP ONE", 0.1, 0.0, group="b"), L.ScreenText((0.12, 0.12), "OVERLAP TWO", 0.1, 0.0, group="c")]
        sc = L.Scene(self.img, [dict(t=0, center=(600, 337), height=600), dict(t=1.5, center=(600, 337), height=600)], size=(640, 360), overlays=ov)
        r = [i["check"] for i in Q.check_overlays(sc)]; self.assertIn("overlay_outside_safe_frame", r); self.assertIn("overlay_collision", r)


class TestEndToEnd(unittest.TestCase):
    def test_rendered_sequence_passes_video_qa(self):
        import os, tempfile
        img, _ = S.islands((1200, 675), 3)
        mk = lambda x: L.Scene(img, [dict(t=0, center=(x, 300), height=400), dict(t=2, center=(x + 120, 330), height=330)], size=(320, 180))
        seq = SQ.Sequence([SQ.Shot(mk(350), 2.0), SQ.Shot(mk(800), 2.0), SQ.Shot(mk(500), 2.0)], [TR.Push("left", duration=0.5), TR.CinematicPush(duration=0.6)])
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "t.mp4"); SQ.render_video(seq, out, fps=30, workers=2, log=None)
            r = Q.run_video(out, Q.QAConfig(size=(160, 90)), schedule=seq.schedule(), problems=seq.problems)
        self.assertTrue(r["ok"], r["issues"]); self.assertGreater(r["stats"]["frames"], 140)


if __name__ == "__main__":
    unittest.main()
