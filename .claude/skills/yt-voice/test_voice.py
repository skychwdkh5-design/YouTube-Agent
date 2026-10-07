#!/usr/bin/env python3
"""Offline tests for voice.py - ElevenLabs is mocked, nothing leaves the machine, no key needed.
The mocked provider returns real MP3 bytes made by the local ffmpeg (those tests skip without it).

    python3 test_voice.py
"""
import base64, io, json, os, shutil, subprocess, sys, tempfile, unittest, urllib.error
from contextlib import redirect_stdout
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voice as v

HAVE_FF = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
FAKE_KEY = "sk_fake_ELEVEN_key_0123456789"
VOICE = "TestVoice01"
_MP3 = {}


def mp3(seconds):
    if seconds not in _MP3:
        d = tempfile.mkdtemp(); p = os.path.join(d, "a.mp3")
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"sine=f=220:d={seconds}",
                        "-ar", "44100", "-c:a", "libmp3lame", p], check=True)
        with open(p, "rb") as f: _MP3[seconds] = f.read()
        shutil.rmtree(d)
    return _MP3[seconds]


def alignment(text, seconds):
    step = seconds / max(len(text), 1)
    return {"characters": list(text),
            "character_start_times_seconds": [round(i * step, 3) for i in range(len(text))],
            "character_end_times_seconds": [round((i + 1) * step, 3) for i in range(len(text))]}


class FakeResp(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): self.close()


def eleven(seconds=1.0, body=None, error=None, align=True, requests=None):
    """A urlopen replacement that answers like the ElevenLabs with-timestamps endpoint."""
    def urlopen(req, timeout=None):
        payload = json.loads(req.data)
        if requests is not None:
            requests.append({"url": req.full_url, "headers": dict(req.header_items()), "body": payload})
        if error: raise error
        if body is not None: return FakeResp(body)
        d = {"audio_base64": base64.b64encode(mp3(seconds)).decode()}
        if align: d["alignment"] = alignment(payload["text"], seconds)
        return FakeResp(json.dumps(d).encode())
    return urlopen


def run(argv, urlopen=None, key=FAKE_KEY):
    buf = io.StringIO()
    env = {"ELEVENLABS_API_KEY": key} if key is not None else {}
    with mock.patch.dict(os.environ, env, clear=False), redirect_stdout(buf):
        if key is None: os.environ.pop("ELEVENLABS_API_KEY", None)
        if urlopen:
            with mock.patch.object(v.urllib.request, "urlopen", urlopen):
                code = v.main(argv)
        else:
            with mock.patch.object(v.urllib.request, "urlopen", side_effect=AssertionError("network!")):
                code = v.main(argv)
    out = buf.getvalue()
    return code, json.loads(out), out


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.out = os.path.join(self.dir, "narration.wav")

    def args(self, text="Hello there, world. This is a test.", *extra):
        return ["--text", text, "--voice-id", VOICE, "--output", self.out, *extra]

    def assertClean(self):
        self.assertEqual(sorted(os.listdir(self.dir)), [], "a failed run left files behind")


class Script(unittest.TestCase):
    def test_spoken_text_strips_directions_keeps_words(self):
        raw = ("# Hook\n\n**Lake Mead is losing water.** [ON SCREEN: Landsat 2000 vs 2022]\n"
               "- It dropped 150 feet, about 46 m.\n\n## Beat 2\n[B-ROLL: dam]\nWhy? Read on...")
        text, removed = v.spoken_text(raw)
        self.assertEqual(text, "Lake Mead is losing water. It dropped 150 feet, about 46 m.\n\nWhy? Read on...")
        self.assertIn("[ON SCREEN: Landsat 2000 vs 2022]", removed)
        self.assertIn("# Hook", removed)

    def test_chunks_respect_limit_and_keep_text(self):
        text = " ".join(f"Sentence number {i} is here." for i in range(60))
        chunks = v.split_chunks(text, 200)
        self.assertTrue(all(len(c) <= 200 for c in chunks))
        self.assertEqual(" ".join(chunks).split(), text.split())

    def test_alignment_mismatch_gives_no_timing(self):
        a = alignment("Hello world", 1.0)
        self.assertIsNone(v.words_from_alignment("Hello there", {"characters": a["characters"],
                          "start": a["character_start_times_seconds"], "end": a["character_end_times_seconds"]}, 0))

    def test_word_timing_from_characters(self):
        a = alignment("Hi, you.", 0.8)
        w = v.words_from_alignment("Hi, you.", {"characters": a["characters"],
                                   "start": a["character_start_times_seconds"],
                                   "end": a["character_end_times_seconds"]}, 10.0)
        self.assertEqual([x["text"] for x in w], ["Hi,", "you."])
        self.assertEqual((w[0]["start"], w[1]["end"]), (10.0, 10.8))

    def test_bad_timing_values_rejected(self):
        bad = {"characters": list("ab"), "start": [0.5, 0.1], "end": [0.4, 0.2]}
        self.assertIsNone(v.words_from_alignment("ab", bad, 0))
        self.assertIsNone(v.words_from_alignment("ab", {"characters": list("ab"), "start": ["x", 1], "end": [1, 2]}, 0))


class Guards(Base):
    def test_needs_confirm_and_sends_nothing(self):
        code, d, _ = run(self.args())
        self.assertEqual((code, d["status"]), (2, "confirm_required"))
        self.assertEqual(d["characters"], len("Hello there, world. This is a test."))
        self.assertClean()

    def test_character_limit_blocks_before_request(self):
        code, d, _ = run(self.args("x" * 100, "--confirm", "--max-chars", "50"))
        self.assertEqual((code, d["status"], d["characters"]), (2, "over_limit", 100))
        self.assertClean()

    def test_missing_api_key(self):
        code, d, _ = run(self.args("Hello.", "--confirm"), key=None)
        self.assertEqual((code, d["status"]), (2, "missing_credentials"))
        self.assertIn("ELEVENLABS_API_KEY", d["error"])
        self.assertClean()

    def test_bad_arguments_are_json(self):
        for argv in (["--text", "hi", "--voice-id", "../../etc", "--output", self.out],
                     ["--text", "hi", "--voice-id", VOICE, "--output", "x.ogg"],
                     ["--text", "hi", "--voice-id", VOICE, "--output", self.out, "--max-chars", "x"],
                     ["--text", "hi", "--voice-id", VOICE, "--output", self.out, "--provider", "nope"],
                     ["--voice-id", VOICE, "--output", self.out],
                     ["--text", "hi", "--voice-id", VOICE, "--output", self.out, "--bogus"],
                     ["--text", "[ON SCREEN: only a direction]", "--voice-id", VOICE, "--output", self.out]):
            code, d, out = run(argv)
            self.assertEqual(code, 2, argv)
            self.assertIn("error", d); self.assertNotIn("Traceback", out)


@unittest.skipUnless(HAVE_FF, "ffmpeg not installed")
class Generation(Base):
    def test_success_with_timing(self):
        reqs = []
        code, d, out = run(self.args("Hello there, world. This is a test.", "--confirm"),
                           eleven(1.5, requests=reqs))
        self.assertEqual((code, d["status"], d["timing"]), (0, "ok", True), d)
        self.assertNotIn(FAKE_KEY, out)
        self.assertEqual(reqs[0]["headers"].get("Xi-api-key"), FAKE_KEY)  # sent only as the header
        self.assertIn(f"/v1/text-to-speech/{VOICE}/with-timestamps", reqs[0]["url"])
        meta = json.load(open(os.path.join(self.dir, "narration.voice.json")))
        self.assertEqual(meta["schema"], "yt-voice/1")
        self.assertEqual([w["text"] for w in meta["words"]],
                         ["Hello", "there,", "world.", "This", "is", "a", "test."])
        self.assertAlmostEqual(meta["duration"], 1.5, delta=0.1)
        self.assertNotIn(FAKE_KEY, json.dumps(meta))
        self.assertEqual(sorted(os.listdir(self.dir)), ["narration.voice.json", "narration.wav"])

    def test_multi_chunk_offsets(self):
        text = "First paragraph is here.\n\nSecond paragraph follows it."
        code, d, _ = run(["--text", text, "--voice-id", VOICE, "--output", self.out, "--confirm",
                          "--max-chunk-chars", "50"], eleven(1.0))
        self.assertEqual((code, d["chunks"]), (0, 2), d)
        meta = json.load(open(os.path.join(self.dir, "narration.voice.json")))
        self.assertAlmostEqual(meta["chunks"][1]["offset"], meta["chunks"][0]["duration"], places=3)
        second = [w for w in meta["words"] if w["text"] == "Second"][0]
        self.assertGreaterEqual(second["start"], meta["chunks"][1]["offset"])
        starts = [w["start"] for w in meta["words"]]
        self.assertEqual(starts, sorted(starts))

    def test_proxy_auth_sends_no_key_and_needs_no_env(self):
        reqs = []
        code, d, out = run(self.args("Hello.", "--confirm", "--auth", "proxy"), eleven(0.5, requests=reqs),
                           key=None)
        self.assertEqual((code, d["status"]), (0, "ok"), d)
        self.assertNotIn("Xi-api-key", reqs[0]["headers"])

    def test_proxy_auth_ignores_env_key(self):
        reqs = []
        with mock.patch.dict(os.environ, {"YT_VOICE_AUTH": "proxy"}):
            code, d, out = run(self.args("Hello.", "--confirm"), eleven(0.5, requests=reqs))
        self.assertEqual(code, 0, d)
        self.assertNotIn("Xi-api-key", reqs[0]["headers"])
        self.assertNotIn(FAKE_KEY, out)

    def test_bad_auth_mode(self):
        code, d, _ = run(self.args("Hello.", "--confirm", "--auth", "cookie"), eleven(0.5))
        self.assertEqual(code, 2); self.assertIn("--auth", d["error"])

    def test_no_alignment_means_no_timing(self):
        code, d, _ = run(self.args("Hello.", "--confirm"), eleven(0.5, align=False))
        self.assertEqual((code, d["timing"], d["words"]), (0, False, 0))
        self.assertTrue(d["warnings"])

    def test_mp3_output(self):
        self.out = os.path.join(self.dir, "narration.mp3")
        code, d, _ = run(self.args("Hello.", "--confirm"), eleven(0.5))
        self.assertEqual(code, 0, d)
        self.assertTrue(os.path.getsize(self.out) > 1000)

    def test_no_overwrite(self):
        with open(self.out, "w") as f: f.write("keep")
        code, d, _ = run(self.args("Hello.", "--confirm"), eleven(0.5))
        self.assertEqual((code, d["status"]), (2, "exists"))
        with open(self.out) as f: self.assertEqual(f.read(), "keep")
        self.assertEqual(run(self.args("Hello.", "--confirm", "--overwrite"), eleven(0.5))[0], 0)


class Failures(Base):
    def test_malformed_responses(self):
        for body in (b"not json", json.dumps({"nope": 1}).encode(),
                     json.dumps({"audio_base64": "!!notbase64!!"}).encode(),
                     json.dumps({"audio_base64": ""}).encode()):
            code, d, _ = run(self.args("Hello.", "--confirm"), eleven(body=body))
            self.assertEqual((code, d["status"]), (2, "malformed_response"), body)
            self.assertClean()

    def test_undecodable_audio_cleaned_up(self):
        if not HAVE_FF: self.skipTest("ffmpeg not installed")
        body = json.dumps({"audio_base64": base64.b64encode(b"garbage" * 50).decode()}).encode()
        code, d, _ = run(self.args("Hello.", "--confirm"), eleven(body=body))
        self.assertEqual((code, d["status"]), (2, "audio_error"))
        self.assertClean()

    def test_network_failure(self):
        for err in (urllib.error.URLError("no route"), TimeoutError("timed out"), ConnectionResetError("reset")):
            code, d, _ = run(self.args("Hello.", "--confirm"), eleven(error=err))
            self.assertEqual((code, d["status"]), (2, "network_error"), err)
            self.assertClean()

    def test_http_error_redacts_key(self):
        err = urllib.error.HTTPError("u", 401, "Unauthorized", {},
                                     io.BytesIO(json.dumps({"detail": {"status": "invalid_api_key",
                                                "message": f"key {FAKE_KEY} is invalid"}}).encode()))
        code, d, out = run(self.args("Hello.", "--confirm"), eleven(error=err))
        self.assertEqual((code, d["status"]), (2, "provider_error"))
        self.assertIn("401", d["error"]); self.assertIn("[REDACTED]", d["error"])
        self.assertNotIn(FAKE_KEY, out)
        self.assertClean()

    def test_failure_in_second_chunk_leaves_nothing(self):
        if not HAVE_FF: self.skipTest("ffmpeg not installed")
        ok, calls = eleven(0.5), []

        def flaky(req, timeout=None):
            calls.append(1)
            if len(calls) == 2: raise urllib.error.URLError("dropped")
            return ok(req, timeout)
        code, d, _ = run(["--text", "First paragraph is right here.\n\nSecond paragraph is right here.", "--voice-id", VOICE,
                          "--output", self.out, "--confirm", "--max-chunk-chars", "50"], flaky)
        self.assertEqual((code, d["status"], len(calls)), (2, "network_error", 2))
        self.assertClean()

    def test_unexpected_exception_redacted(self):
        def boom(req, timeout=None): raise RuntimeError(f"weird {FAKE_KEY}")
        code, d, out = run(self.args("Hello.", "--confirm"), boom)
        self.assertEqual(code, 2); self.assertNotIn(FAKE_KEY, out)
        self.assertClean()


if __name__ == "__main__":
    unittest.main(verbosity=1)
