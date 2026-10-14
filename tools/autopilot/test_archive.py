#!/usr/bin/env python3
"""Archive and recovery tests: small files, tiny part size - the logic is the same as for a 270 MB master."""
import base64, hashlib, json, os, shutil, subprocess, sys, tempfile, unittest, wave, struct

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import archive, recover_narration  # noqa: E402

HAVE_FF = bool(shutil.which("ffmpeg"))


def w(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb" if isinstance(data, bytes) else "w") as f: f.write(data)


class Archive(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.prod = os.path.join(self.tmp.name, "ep994-x")
        self.master = os.urandom(5000)
        w(self.prod + "/final.mp4", self.master)
        w(self.prod + "/voice/narration.voice.json", json.dumps({"schema": "yt-voice/1"}))
        w(self.prod + "/voice/cache/abc.json", json.dumps({"audio_base64": "AAAA"}))
        w(self.prod + "/release/description.txt", "d")
        w(self.prod + "/timeline.json", "{}")
        self.out = os.path.join(self.tmp.name, "arch")

    def test_create_splits_large_files_and_hashes_everything(self):
        r = archive.create(self.prod, self.out, part_bytes=2000, with_cache=True)
        self.assertTrue(r["ok"]); self.assertEqual(r["split"], 1)
        m = json.load(open(self.out + "/ARCHIVE_MANIFEST.json"))
        e = next(x for x in m["files"] if x["path"] == "final.mp4")
        self.assertEqual([p["bytes"] for p in e["parts"]], [2000, 2000, 1000])
        self.assertEqual(e["sha256"], hashlib.sha256(self.master).hexdigest())
        sums = open(self.out + "/SHA256SUMS").read()
        self.assertIn("final.mp4.part00", sums); self.assertIn("voice/cache/abc.json", sums)
        self.assertEqual(sorted(x["role"] for x in m["files"])[0], "build")        # roles recorded
        self.assertTrue(any(x["role"] == "paid" for x in m["files"]))

    def test_sha256sum_tool_agrees_with_the_archive(self):
        archive.create(self.prod, self.out, part_bytes=2000)
        p = subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=self.out, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_verify_passes_then_catches_corruption_and_loss(self):
        archive.create(self.prod, self.out, part_bytes=2000)
        self.assertTrue(archive.verify(self.out)["ok"])
        part = self.out + "/final.mp4.part01"
        data = open(part, "rb").read(); w(part, data[:-1] + bytes([data[-1] ^ 1]))
        v = archive.verify(self.out); self.assertFalse(v["ok"]); self.assertTrue(any("part01" in p for p in v["problems"]))
        w(part, data)
        os.remove(self.out + "/final.mp4.part02")
        v = archive.verify(self.out); self.assertFalse(v["ok"]); self.assertTrue(any("missing part" in p for p in v["problems"]))

    def test_restore_after_total_loss_reproduces_the_master_bit_for_bit(self):
        archive.create(self.prod, self.out, part_bytes=2000, with_cache=True)
        shutil.rmtree(self.prod)                                       # the container is gone
        dest = os.path.join(self.tmp.name, "restored")
        r = archive.restore(self.out, dest)
        self.assertEqual(open(dest + "/final.mp4", "rb").read(), self.master)
        self.assertTrue(os.path.exists(dest + "/voice/cache/abc.json"))

    def test_nothing_is_ever_overwritten(self):
        archive.create(self.prod, self.out, part_bytes=2000)
        with self.assertRaises(ValueError): archive.create(self.prod, self.out, part_bytes=2000)
        dest = os.path.join(self.tmp.name, "d"); os.makedirs(dest); w(dest + "/keep", "x")
        with self.assertRaises(ValueError): archive.restore(self.out, dest)

    def test_a_corrupt_archive_refuses_to_restore(self):
        archive.create(self.prod, self.out, part_bytes=2000)
        w(self.out + "/final.mp4.part00", os.urandom(2000))
        with self.assertRaises(ValueError): archive.restore(self.out, os.path.join(self.tmp.name, "r"))

    def test_recoverable_report(self):
        self.assertTrue(archive.recoverable(self.prod)["recoverable_without_paying"])
        shutil.rmtree(self.prod + "/voice/cache")
        r = archive.recoverable(self.prod)
        self.assertFalse(r["recoverable_without_paying"]); self.assertIn("paid again", r["how"])


@unittest.skipUnless(HAVE_FF, "ffmpeg not installed")
class NarrationRecovery(unittest.TestCase):
    """The paid responses are enough to rebuild the narration with no API call; the result is checked against the recorded hash."""

    def test_rebuild_from_cache_in_both_layouts_is_byte_identical(self):
        sys.path.insert(0, os.path.join(HERE, "..", "..", ".claude", "skills", "yt-voice"))
        import voice as v
        with tempfile.TemporaryDirectory() as t:
            cache = os.path.join(t, "cache"); os.makedirs(cache)
            texts = ["First chunk of narration.", "Second chunk follows here."]
            parts, offset, words, chunks = [], 0.0, [], []
            for i, tx in enumerate(texts):
                mp3 = os.path.join(t, f"c{i}.mp3")                      # a real, tiny MP3 made locally
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=frequency={300 + 100 * i}:duration=1.5", "-c:a", "libmp3lame", mp3], check=True)
                step = 1.5 / len(tx)
                al = {"characters": list(tx), "start": [round(k * step, 3) for k in range(len(tx))],
                      "end": [round((k + 1) * step, 3) for k in range(len(tx))]}          # the normalised alignment yt-voice caches
                if i == 0:                                              # current layout: audio inside the json
                    w(os.path.join(cache, f"k{i}.json"), json.dumps({"audio_base64": base64.b64encode(open(mp3, "rb").read()).decode(), "format": "mp3_44100_128", "alignment": al}))
                else:                                                   # EP001-era layout: mp3 next to the json
                    w(os.path.join(cache, f"k{i}.json"), json.dumps({"alignment": al})); shutil.copyfile(mp3, os.path.join(cache, f"k{i}.mp3"))
                wav = os.path.join(t, f"c{i}.wav"); v.to_wav(mp3, wav)
                dur = v.wav_duration(wav); ww = v.words_from_alignment(tx, al, offset); words += ww
                chunks.append({"index": i, "characters": len(tx), "offset": round(offset, 3), "duration": round(dur, 3), "timing": True})
                parts.append(wav); offset += dur
            joined = os.path.join(t, "orig.wav"); v.join_wavs(parts, joined)
            meta = {"text": "\n\n".join(texts), "characters": sum(len(x) for x in texts), "chunks": chunks, "words": words,
                    "audio_sha256": archive.sha256_file(joined), "duration": round(v.wav_duration(joined), 3)}
            w(os.path.join(t, "meta.json"), json.dumps(meta))
            r = recover_narration.recover(os.path.join(t, "meta.json"), cache, os.path.join(t, "out"))
            self.assertTrue(r["byte_identical_wav"], r); self.assertTrue(r["word_timings_identical"])
            self.assertTrue(r["result"].startswith("PROVEN"))
            self.assertEqual(archive.sha256_file(os.path.join(t, "out", "narration.wav")), meta["audio_sha256"])

    def test_missing_response_is_reported_as_incomplete_never_guessed(self):
        with tempfile.TemporaryDirectory() as t:
            cache = os.path.join(t, "cache"); os.makedirs(cache)
            meta = {"text": "Only chunk.", "characters": 11, "chunks": [{"index": 0, "characters": 11, "offset": 0.0, "duration": 1.0, "timing": True}], "words": [], "audio_sha256": "x", "duration": 1.0}
            w(os.path.join(t, "meta.json"), json.dumps(meta))
            r = recover_narration.recover(os.path.join(t, "meta.json"), cache, os.path.join(t, "out"))
            self.assertTrue(r["result"].startswith("INCOMPLETE")); self.assertEqual(r["chunks_matched"], 0)

    def test_output_directory_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as t:
            os.makedirs(os.path.join(t, "out")); w(os.path.join(t, "out", "x"), "keep")
            w(os.path.join(t, "meta.json"), json.dumps({"text": "a", "characters": 1, "chunks": [{"characters": 1}]}))
            with self.assertRaises(ValueError): recover_narration.recover(os.path.join(t, "meta.json"), t, os.path.join(t, "out"))


if __name__ == "__main__":
    unittest.main()
