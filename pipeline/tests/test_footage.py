import os, subprocess, sys, tempfile, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import footage  # noqa: E402


def make(path, moving, seconds=4):
    src = "testsrc2=size=320x180:rate=30" if moving else "color=c=gray:size=320x180:rate=30"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", src, "-t", str(seconds), "-pix_fmt", "yuv420p", path], check=True)


class FootageGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = tempfile.mkdtemp()
        make(os.path.join(cls.d, "live.mp4"), True)
        make(os.path.join(cls.d, "static.mp4"), False)

    def tl(self, layers):
        shots = [{"id": "cover", "start": 0, "layers": [{"type": "graphic", "asset": "cover"}]}]
        t = 0.0333
        for i, L in enumerate(layers):
            shots.append({"id": f"s{i}", "start": t, "layers": [L]}); t += 4
        return {"assets": {"cover": {"src": "c.png"}, "live": {"src": "live.mp4"}, "static": {"src": "static.mp4"},
                           "img": {"src": "i.png"}}, "shots": shots, "end": {"seconds": t}}

    def test_live_moving_passes(self):
        tl = self.tl([{"type": "video", "asset": "live", "trim": 0}] * 2)
        m = footage.measure(tl, {"assets": [{"src": "live.mp4", "footage": "live"}]}, 8.03, self.d)
        self.assertTrue(m["ok"], m)

    def test_static_video_declared_live_fails(self):
        tl = self.tl([{"type": "video", "asset": "static", "trim": 0}] * 2)
        m = footage.measure(tl, {"assets": [{"src": "static.mp4", "footage": "live"}]}, 8.03, self.d)
        self.assertFalse(m["ok"], m)

    def test_undeclared_and_animation_do_not_count(self):
        tl = self.tl([{"type": "video", "asset": "live", "trim": 0}] * 2)
        self.assertFalse(footage.measure(tl, {"assets": []}, 8.03, self.d)["ok"])
        self.assertFalse(footage.measure(tl, {"assets": [{"src": "live.mp4", "footage": "animation"}]}, 8.03, self.d)["ok"])

    def test_still_never_counts(self):
        tl = self.tl([{"type": "still", "asset": "img"}, {"type": "video", "asset": "live", "trim": 0}])
        m = footage.measure(tl, {"assets": [{"src": "i.png", "footage": "live"}, {"src": "live.mp4", "footage": "live"}]}, 8.03, self.d)
        self.assertAlmostEqual(m["live_share"], 0.5, delta=0.05)
        self.assertFalse(m["ok"])


if __name__ == "__main__":
    unittest.main()
