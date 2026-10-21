#!/usr/bin/env python3
import json, os, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vshort as v


class VShort(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        words = [{"text": t, "start": 1.0 + i * 0.4, "end": 1.0 + i * 0.4 + 0.3} for i, t in enumerate("The sea fell. It kept falling. Then it stopped.".split())]
        json.dump({"words": words}, open(os.path.join(self.d, "v.json"), "w"))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=blue:s=640x360:r=30:d=14", "-f", "lavfi", "-i", "sine=frequency=300:d=14", "-shortest",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", os.path.join(self.d, "src.mp4")], check=True)
        self.spec = {"source": {"video": os.path.join(self.d, "src.mp4"), "voice_json": os.path.join(self.d, "v.json")}, "t0": 0.5, "t1": 9.0, "crop": [0, 0, 640, 300],
                     "hook": {"text": "THE SEA\nFELL", "accent": "FELL", "seconds": 2.0}, "kicks": [{"at": 4, "text": "a very long kick line that must still fit the width"}],
                     "chip": "test", "endcard": {"title": "Full\nepisode", "line": "OrbitalAtlas", "seconds": 2.0}}

    def test_captions_are_exactly_the_narration_words(self):
        words = v.words_in(self.spec["source"]["voice_json"], 0.5, 9.0)
        a = v.ass(self.spec, words)
        for w in words:
            self.assertIn(w["text"].upper(), a)
        self.assertNotIn("ELEVENLABS", a)
        self.assertIn("FELL", a)

    def test_hook_and_kick_fit_the_safe_width(self):
        a = v.ass(self.spec, v.words_in(self.spec["source"]["voice_json"], 0.5, 9.0))
        import re
        for fs in map(int, re.findall(r"\\fs(\d+)", a)):
            self.assertLessEqual(fs, 112)
        self.assertGreater(len(re.findall(r"Dialogue: 2", a)), 1)

    def test_duration_limits_and_missing_words(self):
        bad = dict(self.spec, t1=0.9)
        with self.assertRaises(SystemExit):
            v.validate(bad)
        with self.assertRaises(SystemExit):
            v.words_in(self.spec["source"]["voice_json"], 30, 40)

    def test_render_makes_1080x1920_30fps_with_audio(self):
        out = os.path.join(self.d, "o.mp4")
        r = v.build(self.spec, out)
        p = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate:format=duration", "-of", "json", out], capture_output=True, text=True).stdout)
        vs = [s for s in p["streams"] if s["codec_type"] == "video"][0]
        self.assertEqual((vs["width"], vs["height"], vs["r_frame_rate"]), (1080, 1920, "30/1"))
        self.assertTrue(any(s["codec_type"] == "audio" for s in p["streams"]))
        self.assertAlmostEqual(float(p["format"]["duration"]), r["seconds"], delta=0.2)


if __name__ == "__main__":
    unittest.main()
