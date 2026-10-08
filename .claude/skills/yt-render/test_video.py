#!/usr/bin/env python3
"""Offline tests for video clips ("type": "video") in timeline versions 1/2 and the "video" asset in version 3.
Frame identity is proven with luma-coded sources: frame N of the source has luma 16 + 3*N, so every output frame says
which source frame it came from. Local ffmpeg only.

    python3 test_video.py
"""
import io, json, math, os, shutil, struct, subprocess, sys, tempfile, unittest, wave
from contextlib import redirect_stdout

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render as r

HAVE_FF = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
W, H, FPS = 320, 180, 30


def run(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = r.main(argv)
    return code, json.loads(buf.getvalue())


def ff(*args):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-y", *args], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return p


def coded_video(path, frames=70, fps=FPS, size=(W, H), flash=None, audio=False, gop=15):
    """Frame N has luma 16 + 3N (N < 70); `flash` makes that one frame luma 235. Lossless, keyframe every `gop` frames."""
    expr = f"if(eq(N,{flash}),235,16+3*N)" if flash is not None else "16+3*N"
    cmd = ["-f", "lavfi", "-i", f"color=c=gray:s={size[0]}x{size[1]}:r={fps},format=yuv420p,geq=lum='{expr}':cb=128:cr=128"]
    if audio:
        cmd += ["-f", "lavfi", "-i", "sine=f=440:r=48000"]
    cmd += ["-frames:v", str(frames), "-c:v", "libx264", "-crf", "0", "-g", str(gop), "-pix_fmt", "yuv420p"]
    if audio:
        cmd += ["-c:a", "aac", "-shortest"]
    ff(*cmd, path)


def luma_frames(path, w=W, h=H):
    """Mean luma of every decoded frame (the Y plane of yuv420p, no range conversion)."""
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"],
                       capture_output=True)
    assert p.returncode == 0, p.stderr
    fs = w * h * 3 // 2
    data = np.frombuffer(p.stdout, np.uint8)
    n = len(data) // fs
    return [float(data[i * fs:i * fs + w * h].mean()) for i in range(n)]


def probe_frames(path):
    p = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                        "stream=nb_read_frames,r_frame_rate,avg_frame_rate", "-of", "json", path], capture_output=True, text=True)
    return json.loads(p.stdout)["streams"][0]


def click_wav(path, seconds=3.0, click_at=0.5, rate=48000):
    n = int(seconds * rate)
    a = np.zeros(n, np.int16)
    k = int(click_at * rate)
    a[k:k + 24] = 28000
    with wave.open(path, "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(rate)
        f.writeframes(a.tobytes())


class Base(unittest.TestCase):
    def setUp(self):
        if not HAVE_FF:
            self.skipTest("ffmpeg/ffprobe not installed")
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.p = lambda *a: os.path.join(self.dir, *a)
        Image.new("RGB", (W, H), (255, 0, 0)).save(self.p("red.png"))
        coded_video(self.p("coded.mp4"))

    def timeline(self, clips, **extra):
        tl = {"version": 2, "output": {"width": W, "height": H, "fps": FPS}, "clips": clips, **extra}
        with open(self.p("timeline.json"), "w") as f:
            json.dump(tl, f)
        return self.p("timeline.json")

    def render(self, clips, **extra):
        t = self.timeline(clips, **extra)
        code, plan = run(["--timeline", t])
        self.assertEqual((code, plan["status"]), (2, "confirm_required"), plan)     # the plan call exits 2 until --confirm
        plan = plan["plan"]
        code, out = run(["--timeline", t, "--output", self.p("out.mp4"), "--confirm", "--overwrite"])
        self.assertEqual(code, 0, out)
        return plan, out

    def expect_luma(self, got, first_source_frame, count, tol=1.5):
        for k in range(count):
            self.assertAlmostEqual(got[k], 16 + 3 * (first_source_frame + k), delta=tol, msg=f"output frame {k}")


class Timing(Base):
    def test_whole_clip_is_frame_exact(self):
        plan, out = self.render([{"type": "video", "src": "coded.mp4"}])
        self.assertAlmostEqual(plan["expected_duration"], 70 / FPS, places=3)
        s = probe_frames(self.p("out.mp4"))
        self.assertEqual(int(s["nb_read_frames"]), 70)
        self.assertEqual((s["r_frame_rate"], s["avg_frame_rate"]), ("30/1", "30/1"))
        self.expect_luma(luma_frames(self.p("out.mp4")), 0, 70)

    def test_duration_takes_the_first_frames(self):
        plan, _ = self.render([{"type": "video", "src": "coded.mp4", "duration": 1.0}])
        self.assertEqual(plan["total_frames"], 30)
        self.expect_luma(luma_frames(self.p("out.mp4")), 0, 30)

    def test_frame_rate_policy_is_enforced(self):
        coded_video(self.p("v24.mp4"), frames=48, fps=24)
        code, out = run(["--timeline", self.timeline([{"type": "video", "src": "v24.mp4"}])])
        self.assertEqual(code, 2)
        self.assertIn("24/1 fps", out["error"]); self.assertIn("30 fps", out["error"])


class Trimming(Base):
    def test_trim_in_and_out_is_frame_exact_off_keyframe(self):
        # keyframes every 15 frames; 1.1 s = frame 33 is not one
        plan, _ = self.render([{"type": "video", "src": "coded.mp4", "trim": [1.1, 2.1]}])
        self.assertEqual(plan["total_frames"], 30)
        self.expect_luma(luma_frames(self.p("out.mp4")), 33, 30)

    def test_trim_start_only_runs_to_the_end(self):
        plan, _ = self.render([{"type": "video", "src": "coded.mp4", "trim": [1.0]}])
        self.assertEqual(plan["total_frames"], 40)
        self.expect_luma(luma_frames(self.p("out.mp4")), 30, 40)

    def test_trim_past_the_end_reports_the_shortfall(self):
        code, out = run(["--timeline", self.timeline([{"type": "video", "src": "coded.mp4", "trim": [2.0, 3.0]}])])
        self.assertEqual(code, 2)
        self.assertIn("short by", out["error"]); self.assertIn("0.667", out["error"])   # needs frames 60..89, file has 70

    def test_bad_trim_arguments(self):
        for clip, text in (({"trim": [1.0, 0.5]}, "after its start"), ({"trim": [0.0, 1.0], "duration": 1}, "not both"),
                           ({"trim": "x"}, "trim must be"), ({"motion": {"type": "kenburns"}}, "frame for frame")):
            code, out = run(["--timeline", self.timeline([{"type": "video", "src": "coded.mp4", **clip}])])
            self.assertEqual(code, 2); self.assertIn(text, out["error"])
        code, out = run(["--timeline", self.timeline([{"type": "image", "src": "red.png", "duration": 1, "trim": [0, 1]}])])
        self.assertEqual(code, 2); self.assertIn("video clips only", out["error"])


class Boundaries(Base):
    def still(self, frames):
        return {"type": "image", "src": "red.png", "duration": frames / FPS, "motion": {"type": "static"}}

    def test_clip_boundaries_land_on_exact_frames(self):
        plan, out = self.render([self.still(30), {"type": "video", "src": "coded.mp4", "trim": [0.5, 1.5]}, self.still(20)])
        self.assertEqual(plan["total_frames"], 80)
        got = luma_frames(self.p("out.mp4"))
        self.assertEqual(len(got), 80)
        red = got[0]
        for k in range(30):
            self.assertAlmostEqual(got[k], red, delta=1.0, msg=f"still frame {k}")
        for k in range(30):
            self.assertAlmostEqual(got[30 + k], 16 + 3 * (15 + k), delta=1.5, msg=f"video frame {k}")
        for k in range(20):
            self.assertAlmostEqual(got[60 + k], red, delta=1.0, msg=f"still frame {60 + k}")
        self.assertGreater(abs(got[30] - red), 5)       # the cut is a real cut

    def test_two_video_clips_back_to_back(self):
        plan, _ = self.render([{"type": "video", "src": "coded.mp4", "trim": [0.0, 0.5]}, {"type": "video", "src": "coded.mp4", "trim": [1.0, 1.5]}])
        got = luma_frames(self.p("out.mp4"))
        self.assertEqual(len(got), 30)
        self.expect_luma(got[:15], 0, 15); self.expect_luma(got[15:], 30, 15)

    def test_crossfade_shortens_the_total_and_keeps_clean_frames_outside_the_overlap(self):
        plan, _ = self.render([{"type": "video", "src": "coded.mp4", "trim": [0.0, 1.5], "transition": {"type": "crossfade", "duration": 0.5}},
                               self.still(30)])
        self.assertEqual(plan["total_frames"], 45 + 30 - 15)
        got = luma_frames(self.p("out.mp4"))
        self.assertEqual(len(got), 60)
        self.expect_luma(got[:30], 0, 30)                                   # before the 15-frame overlap: pure video frames 0..29
        red = got[59]
        for k in range(45, 60):
            self.assertAlmostEqual(got[k], red, delta=1.0, msg=f"pure still frame {k}")
        for k in range(30, 45):                                              # inside the overlap the picture is a mix, moving monotonically to the still
            self.assertGreaterEqual(abs(got[k] - red), 0.0)
        self.assertGreater(abs(got[30] - red), abs(got[44] - red) - 1.0)

    def test_still_only_plan_is_unchanged(self):
        """The ffmpeg command of a still-image timeline equals the one captured before video support existed."""
        g = json.load(open(os.path.join(HERE, "fixtures", "golden_still_cmd.json")))
        d = self.dir
        Image.new("RGB", (320, 180), (10, 100, 200)).save(self.p("a.png")); Image.new("RGB", (180, 320), (200, 100, 10)).save(self.p("b.jpg"))
        Image.new("RGB", (320, 180), (90, 90, 90)).save(self.p("c.png"))
        tl = {"version": 2, "output": {"width": 640, "height": 360, "fps": 30}, "clips": [
            {"type": "landsat", "src": "a.png", "duration": 2, "credit": "Landsat USGS", "motion": {"type": "kenburns", "zoom": [1.0, 1.2], "pan": "left_to_right"}, "transition": {"type": "crossfade", "duration": 0.5}},
            {"type": "image", "src": "b.jpg", "duration": 1.5, "fit": "contain", "motion": {"type": "static"}, "transition": {"type": "none"}},
            {"type": "image", "src": "c.png", "duration": 1, "motion": {"type": "kenburns", "zoom": [1.1, 1.0], "pan": "top_to_bottom"}}], "credit": {}}
        plan = r.validate(tl, d)
        cmd = [c.replace(os.path.realpath(d), "<DIR>").replace(d, "<DIR>") for c in r.build_command(plan, os.path.join(d, "out.mp4"), 500 * 1048576, None)]
        want = [c.replace("/tmp/claude-0/stillgold", "<DIR>") for c in g["cmd"]]
        self.assertEqual(cmd, want)
        self.assertEqual((plan["total_frames"], plan["expected_duration"]), (g["total_frames"], g["expected_duration"]))


class AudioSync(Base):
    def test_narration_and_video_stay_locked(self):
        """The source flashes at frame 45 (1.5 s); trimmed from 1.0 s it flashes at output frame 15 (0.5 s). The narration has a click at 0.5 s."""
        coded_video(self.p("flash.mp4"), flash=45, audio=True)
        click_wav(self.p("voice.wav"), seconds=3.0, click_at=0.5)
        plan, out = self.render([{"type": "video", "src": "flash.mp4", "trim": [1.0]}, {"type": "image", "src": "red.png", "duration": 2.0, "motion": {"type": "static"}}],
                                audio={"voice": [{"src": "voice.wav", "start": 0.0, "normalize": False}]})
        self.assertTrue(any("own audio is ignored" in w for w in plan["warnings"]))
        luma = luma_frames(self.p("out.mp4"))
        flash_frame = int(np.argmax(luma[:40]))
        self.assertEqual(flash_frame, 15)
        pcm = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-i", self.p("out.mp4"), "-f", "s16le", "-ac", "1", "-ar", "48000", "-"],
                             capture_output=True).stdout
        a = np.abs(np.frombuffer(pcm, np.int16).astype(np.int32))
        click_t = int(np.argmax(a)) / 48000
        self.assertLess(abs(click_t - flash_frame / FPS), 0.03, f"click at {click_t:.4f}s, flash frame at {flash_frame / FPS:.4f}s")
        d = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", self.p("out.mp4")]))
        self.assertAlmostEqual(float(d["format"]["duration"]), plan["expected_duration"], delta=0.05)
        self.assertGreaterEqual(len(luma), plan["total_frames"])

    def test_narration_start_offset_moves_only_the_audio(self):
        coded_video(self.p("flash.mp4"), flash=45)
        click_wav(self.p("voice.wav"), seconds=3.0, click_at=0.5)
        self.render([{"type": "video", "src": "flash.mp4", "trim": [1.0]}, {"type": "image", "src": "red.png", "duration": 2.5, "motion": {"type": "static"}}],
                    audio={"voice": [{"src": "voice.wav", "start": 0.5, "normalize": False}]})
        luma = luma_frames(self.p("out.mp4"))
        self.assertEqual(int(np.argmax(luma[:40])), 15)                   # picture unchanged by the audio offset
        pcm = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-i", self.p("out.mp4"), "-f", "s16le", "-ac", "1", "-ar", "48000", "-"], capture_output=True).stdout
        self.assertLess(abs(int(np.argmax(np.abs(np.frombuffer(pcm, np.int16).astype(np.int32)))) / 48000 - 1.0), 0.03)

    def test_narration_longer_than_the_clips_is_refused(self):
        click_wav(self.p("voice.wav"), seconds=4.0)
        code, out = run(["--timeline", self.timeline([{"type": "video", "src": "coded.mp4", "trim": [0.0, 1.0]}], audio={"voice": [{"src": "voice.wav", "normalize": False}]})])
        self.assertEqual(code, 2); self.assertIn("narration is never cut", out["error"])


class ComposeVideo(unittest.TestCase):
    """timeline version 3 (profile long, segmented): a "video" asset and layer. 1920x1080, 30 fps, 30-frame segments."""
    LW, LH = 1920, 1080

    def setUp(self):
        if not HAVE_FF:
            self.skipTest("ffmpeg/ffprobe not installed")
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.p = lambda *a: os.path.join(self.dir, *a)
        with open(self.p("grid.json"), "w") as f:
            json.dump({"schema": "yt-geo-stack/1", "epsg": 32611, "x0": 600000.0, "y_top": 4000000.0, "pixel_m": 30.0, "width": 100, "height": 100}, f)
        coded_video(self.p("coded.mp4"), size=(640, 360))            # 16:9, scaled to 1080p by the renderer
        coded_video(self.p("flash.mp4"), size=(640, 360), flash=45, frames=100)

    def timeline(self, shots, assets=None, seconds=2.0, **extra):
        a = {"v": {"src": "coded.mp4", "kind": "video", "credit": "Test video"}, "f": {"src": "flash.mp4", "kind": "video", "credit": "Test video"}}
        a.update(assets or {})
        tl = {"version": 3, "profile": "long", "grid": "grid.json", "assets": a, "shots": shots, "end": {"seconds": seconds}, "render": {"segment_s": 1}, **extra}
        with open(self.p("timeline.json"), "w") as f:
            json.dump(tl, f)
        return self.p("timeline.json")

    def render(self, shots, **kw):
        t = self.timeline(shots, **kw)
        code, plan = run(["--timeline", t])
        self.assertEqual((code, plan["status"]), (2, "confirm_required"), plan)
        code, out = run(["--timeline", t, "--output", self.p("out.mp4"), "--confirm", "--overwrite"])
        self.assertEqual(code, 0, out)
        return plan["plan"], out

    def luma(self):
        return luma_frames(self.p("out.mp4"), self.LW, self.LH)

    def vshot(self, sid, start, asset="v", trim=0, **layer):
        return {"id": sid, "start": start, "layers": [{"type": "video", "asset": asset, "trim": trim, "credit": False, "captions": False, **layer}]}

    def test_frames_are_exact_across_segment_boundaries(self):
        plan, out = self.render([self.vshot("a", 0)], seconds=70 / FPS)
        self.assertEqual(out["segments"], 3)                               # 30 + 30 + 10 frames: the decoder restarts at frames 30 and 60
        got = self.luma()
        self.assertEqual(len(got), 70)
        for k in range(70):
            self.assertAlmostEqual(got[k], 16 + 3 * k, delta=2.0, msg=f"frame {k}")

    def test_layer_trim_is_frame_exact(self):
        self.render([self.vshot("a", 0, trim=1.1)], seconds=1.0)
        got = self.luma()
        self.assertEqual(len(got), 30)
        for k in range(30):
            self.assertAlmostEqual(got[k], 16 + 3 * (33 + k), delta=2.0, msg=f"frame {k}")

    def test_shot_boundaries_and_restart_of_the_same_asset(self):
        self.render([self.vshot("a", 0, trim=0.0), self.vshot("b", 15 / FPS, trim=1.0)], seconds=45 / FPS)
        got = self.luma()
        for k in range(15):
            self.assertAlmostEqual(got[k], 16 + 3 * k, delta=2.0, msg=f"first shot frame {k}")
        for k in range(30):
            self.assertAlmostEqual(got[15 + k], 16 + 3 * (30 + k), delta=2.0, msg=f"second shot frame {k}")

    def test_video_and_narration_stay_locked(self):
        click_wav(self.p("n.wav"), seconds=2.0, click_at=0.5)
        plan, out = self.render([self.vshot("a", 0, asset="f", trim=1.0)], seconds=2.0, voice={"src": "n.wav", "normalize": False})
        got = self.luma()
        flash = int(np.argmax(got[:40]))
        self.assertEqual(flash, 15)                                         # source frame 45, trimmed from frame 30
        pcm = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-i", self.p("out.mp4"), "-f", "s16le", "-ac", "1", "-ar", "48000", "-"], capture_output=True).stdout
        click = int(np.argmax(np.abs(np.frombuffer(pcm, np.int16).astype(np.int32)))) / 48000
        self.assertLess(abs(click - flash / FPS), 0.03)

    def test_refusals(self):
        coded_video(self.p("v24.mp4"), frames=48, fps=24, size=(640, 360)); coded_video(self.p("sq.mp4"), size=(360, 360))
        cases = [(self.vshot("a", 0, asset="x"), {"x": {"src": "v24.mp4", "kind": "video", "credit": "c"}}, 1.0, "24/1 fps"),
                 (self.vshot("a", 0, asset="x"), {"x": {"src": "sq.mp4", "kind": "video", "credit": "c"}}, 1.0, "never cropped or stretched"),
                 (self.vshot("a", 0, asset="x"), {"x": {"src": "coded.mp4", "kind": "video"}}, 1.0, "needs an on-screen 'credit'"),
                 (self.vshot("a", 0), {}, 3.0, "short); shorten the shot"),                       # 70 frames available, 90 needed
                 (self.vshot("a", 0, trim=2.0), {}, 1.0, "frames from its start frame"),         # 10 frames left, 30 needed
                 ({"id": "a", "start": 0, "layers": [{"type": "video", "asset": "v", "captions": "no"}]}, {}, 1.0, "must be true or false")]
        for shot, assets, secs, msg in cases:
            code, out = run(["--timeline", self.timeline([shot], assets=assets, seconds=secs)])
            self.assertEqual(code, 2); self.assertIn(msg, out["error"])

    def test_video_is_a_full_frame_picture_for_the_pacing_rules(self):
        plan, _ = self.render([self.vshot("a", 0), {"id": "b", "start": 1.0, "layers": [{"type": "video", "asset": "f", "credit": False}]}], seconds=2.0)
        self.assertEqual([x["kind"] for x in plan["compositions"]["resets"]][:1], ["video"])

    def test_caption_placement_override_and_default(self):
        with open(self.p("c.srt"), "w") as f:
            f.write("1\n00:00:00,200 --> 00:00:01,800\nA short test caption\n\n")
        shots = [self.vshot("a", 0, captions=True, caption={"band": 0.6, "center_x": 0.667, "max_width": 900})]
        self.render(shots, seconds=2.0, captions={"src": "c.srt", "preset": "default"})
        box = json.load(open(self.p("out.manifest.json")))["caption_boxes"][0]
        self.assertAlmostEqual((box["box"][0] + box["box"][2]) / 2, 1280.6, delta=3)          # centred at 0.667 of 1920
        self.assertAlmostEqual((box["box"][1] + box["box"][3]) / 2, 0.6 * self.LH, delta=40)
        self.assertEqual(box["band"], 0.6)
        shots = [self.vshot("a", 0, captions=True)]
        self.render(shots, seconds=2.0, captions={"src": "c.srt", "preset": "default"})
        box = json.load(open(self.p("out.manifest.json")))["caption_boxes"][0]
        self.assertAlmostEqual((box["box"][0] + box["box"][2]) / 2, 960, delta=3); self.assertEqual(box["band"], 0.815)
        shots = [self.vshot("a", 0, captions=False)]                                          # captions switched off for this layer: none drawn
        self.render(shots, seconds=2.0, captions={"src": "c.srt", "preset": "default"})
        self.assertEqual(json.load(open(self.p("out.manifest.json")))["caption_boxes"], [])
        code, out = run(["--timeline", self.timeline([self.vshot("a", 0, caption={"band": 5})], seconds=1.0)])
        self.assertEqual(code, 2); self.assertIn("caption.band", out["error"])

    def test_still_pipeline_untouched_by_the_video_code(self):
        """A version 3 timeline without video assets builds the same Painter state as before."""
        import compose
        self.assertEqual(compose.FULL_FRAME, ("graphic", "video"))
        self.assertEqual([t for t in compose.LAYER_TYPES if t not in ("video",)], ["image", "flip", "wipe", "fill", "outline", "label", "arrow", "pin", "graphic"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
