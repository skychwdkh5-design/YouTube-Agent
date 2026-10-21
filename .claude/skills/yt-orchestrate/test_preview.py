#!/usr/bin/env python3
import json, os, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import preview as P


def clip(path, secs, size="1280x720", tone=True, src="testsrc2"):
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", (f"{src}:s={size}:r=30:d={secs}" if "=" in src else f"{src}=s={size}:r=30:d={secs}")]
    cmd += (["-f", "lavfi", "-i", f"sine=frequency=300:sample_rate=44100:duration={secs}", "-af", "volume=2.5"] if tone else [])
    subprocess.run(cmd + ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", path], check=True)


class Qc(unittest.TestCase):
    def test_good_clip_passes_and_flags_are_specific(self):
        d = tempfile.mkdtemp(); f = os.path.join(d, "a.mp4"); clip(f, 4)
        q = P.qc(f, 4.0)
        self.assertEqual(q["result"], "PASS", q)

    def test_wrong_size_or_duration_fails(self):
        d = tempfile.mkdtemp(); f = os.path.join(d, "a.mp4"); clip(f, 4, "640x360")
        q = P.qc(f, 10.0)
        bad = {c["id"] for c in q["checks"] if not c["ok"]}
        self.assertEqual(q["result"], "FAIL"); self.assertTrue({"format", "duration"} <= bad)

    def test_a_black_stretch_fails_and_a_long_freeze_only_warns(self):
        d = tempfile.mkdtemp(); f = os.path.join(d, "b.mp4"); clip(f, 3, src="color=c=black")
        q = P.qc(f, 3.0)
        self.assertIn("black_frames", {c["id"] for c in q["checks"] if not c["ok"]})
        g = os.path.join(d, "g.mp4"); clip(g, 8, src="color=c=0x336699")
        q2 = P.qc(g, 8.0)
        self.assertEqual({c["id"] for c in q2["checks"] if not c["ok"]}, {"freeze_over_6s"}); self.assertEqual(q2["result"], "WARN")


class Key(unittest.TestCase):
    def test_chapter_key_changes_with_its_shots_and_not_with_other_chapters(self):
        d = tempfile.mkdtemp()
        os.makedirs(os.path.join(d, "voice")); os.makedirs(os.path.join(d, "captions"))
        open(os.path.join(d, "voice", "narration.wav"), "wb").write(b"w"); open(os.path.join(d, "captions", "captions.srt"), "w").write("c")
        open(os.path.join(d, "a.png"), "wb").write(b"a")
        tl = {"assets": {"a": {"src": "a.png"}}, "shots": [{"start": 0, "layers": [{"asset": "a"}]}, {"start": 30, "layers": [{"asset": "a"}]}], "captions": {}, "end": {}}
        k1 = P.chapter_key(d, tl, 0, 10)
        tl2 = json.loads(json.dumps(tl)); tl2["shots"][1]["layers"][0]["asset"] = "a"; tl2["shots"][1]["start"] = 31
        self.assertEqual(k1, P.chapter_key(d, tl2, 0, 10))                       # a later chapter changed: the first one is unchanged
        tl3 = json.loads(json.dumps(tl)); tl3["shots"][0]["layers"].append({"type": "label"})
        self.assertNotEqual(k1, P.chapter_key(d, tl3, 0, 10))


if __name__ == "__main__":
    unittest.main()
