#!/usr/bin/env python3
"""Offline tests for captions.py - pure Python, no network, no ffmpeg needed.

    python3 test_captions.py
"""
import io, json, os, re, shutil, sys, tempfile, unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import captions as c

CFG = dict(c.DEFAULTS)
TEXT = ("Lake Mead is the largest reservoir in the United States. From orbit, the change is "
        "impossible to miss: a white ring, the bathtub ring, marks where the water used to be. "
        "In 2022, the lake fell to its lowest level since it was filled - about 27% of capacity. "
        "So what happened? And can it come back?")


def timed(text, wps=2.5, gap_after=None):
    """Evenly timed words; gap_after={index: seconds} inserts pauses."""
    words, t = [], 0.0
    for i, w in enumerate(text.split()):
        d = 1 / wps
        words.append({"text": w, "start": round(t, 3), "end": round(t + d * 0.9, 3)})
        t += d + (gap_after or {}).get(i, 0)
    return words


def run(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = c.main(argv)
    return code, json.loads(buf.getvalue())


class Chunking(unittest.TestCase):
    def setUp(self):
        self.words = timed(TEXT)
        self.cues, self.srt, self.vtt, self.report = c.build(self.words, CFG)

    def test_exact_wording_and_punctuation(self):
        self.assertEqual(" ".join(x["text"] for x in self.cues), TEXT)
        for mark in (":", ",", "-", "%", "?", "."):
            self.assertIn(mark, " ".join(x["text"] for x in self.cues))
        self.assertTrue(self.report["wording_preserved"])

    def test_limits(self):
        for x in self.cues:
            self.assertLessEqual(len(x["text"]), CFG["max_chars"])
            self.assertLessEqual((x["words"][-1]["end"] - x["words"][0]["start"]), CFG["max_duration"])

    def test_no_overlaps_and_increasing(self):
        for a, b in zip(self.cues, self.cues[1:]):
            self.assertLess(a["start_ms"], a["end_ms"])
            self.assertLessEqual(a["end_ms"], b["start_ms"])
        self.assertTrue(self.report["no_overlaps"])

    def test_breaks_at_sentence_ends(self):
        ends = [x["text"] for x in self.cues]
        self.assertTrue(any(t.endswith("United States.") for t in ends), ends)
        self.assertTrue(ends[-1].endswith("come back?"))

    def test_pause_breaks_cue(self):
        words = timed("one two three four five six seven eight", gap_after={3: 1.5})
        cues = c.chunk(words, CFG)
        self.assertEqual(cues[0]["text"], "one two three four")

    def test_max_duration_splits_slow_speech(self):
        words = timed("a b c d e f g h i j k l", wps=1)
        cues = c.chunk(words, dict(CFG, max_duration=3.0))
        self.assertTrue(all(x["words"][-1]["end"] - x["words"][0]["start"] <= 3.0 for x in cues))

    def test_min_duration_never_overlaps(self):
        words = [{"text": "Hi.", "start": 0.0, "end": 0.1}, {"text": "There", "start": 0.3, "end": 0.6},
                 {"text": "friend.", "start": 0.6, "end": 0.9}]
        cues, *_ = c.build(words, dict(CFG, max_chars=10))
        self.assertLessEqual(cues[0]["end_ms"], cues[1]["start_ms"])

    def test_overlapping_word_times_still_give_clean_cues(self):
        words = [{"text": "Fast", "start": 0.0, "end": 1.2}, {"text": "talk.", "start": 0.5, "end": 1.4},
                 {"text": "Next", "start": 1.0, "end": 1.6}, {"text": "bit.", "start": 1.6, "end": 2.0}]
        cues, *_ = c.build(words, dict(CFG, max_chars=12))
        for a, b in zip(cues, cues[1:]):
            self.assertLessEqual(a["end_ms"], b["start_ms"])
            self.assertLess(a["start_ms"], a["end_ms"])

    def test_long_single_word_is_its_own_cue(self):
        words = timed("short " + "x" * 30 + " end")
        cues, *_, report = c.build(words, dict(CFG, max_chars=20))
        self.assertIn("x" * 30, [x["text"] for x in cues])
        self.assertTrue(report["warnings"])

    def test_wrap_two_balanced_lines(self):
        lines = c.wrap("From orbit, the change is impossible to miss right now", 2, 84)
        self.assertEqual(len(lines), 2)
        self.assertEqual(" ".join(lines), "From orbit, the change is impossible to miss right now")


class PhraseBreaks(unittest.TestCase):
    """Cue and line breaks land on natural phrase boundaries without touching any timing."""

    def test_proper_noun_runs_stay_together(self):
        text = ("You have probably never noticed it, but the largest saltwater lake in the Western "
                "Hemisphere has a ruler-straight line cut right through it.")
        cues, srt, _, report = c.build(timed(text, wps=2.6), CFG)
        joined = [x["text"] for x in cues]
        self.assertFalse(any(t.endswith("Western") for t in joined), joined)
        self.assertTrue(report["wording_preserved"])
        for b in srt.split("\n\n"):
            self.assertNotRegex(b, r"Western\n")

    def test_no_cue_ends_on_a_function_word_when_avoidable(self):
        text = ("Then, in 1959, a railroad causeway of rock and gravel was finished across the lake. "
                "It changed the water on both sides of the line for good.")
        cues, *_ = c.build(timed(text, wps=2.4), CFG)
        for x in cues[:-1]:
            last = c._bare(x["text"].split()[-1]).lower()
            self.assertNotIn(last, c.GLUE["en"], [y["text"] for y in cues])
        self.assertFalse(any(x["text"] in ("lake.", "lake") for x in cues))      # no orphan

    def test_prefers_clause_marks(self):
        text = "Around the shoreline, pale salt and bare lakebed mark where water once stood."
        cues, *_ = c.build(timed(text, wps=2.5), dict(CFG, max_chars=60))
        self.assertTrue(cues[0]["text"].endswith("shoreline,"), [x["text"] for x in cues])

    def test_timings_untouched(self):
        words = timed(TEXT)
        cues, *_ = c.build(words, CFG)
        flat = [w for x in cues for w in x["words"]]
        self.assertEqual(flat, words)
        for x in cues:
            self.assertEqual(x["start_ms"], round(x["words"][0]["start"] * 1000))

    def test_hard_limits_still_hold_for_long_names(self):
        text = " ".join(["Alpha Beta Gamma Delta Epsilon Zeta Eta Theta Iota Kappa Lambda Mu Nu"] * 2) + "."
        cues, *_ = c.build(timed(text, wps=3), dict(CFG, max_chars=40, max_duration=4.0))
        for x in cues:
            self.assertLessEqual(len(x["text"]), 40)
            self.assertLessEqual(x["words"][-1]["end"] - x["words"][0]["start"], 4.0)

    def test_other_language_uses_punctuation_rules_only(self):
        text = "Hej och välkommen till sjön, som ligger långt uppe i norr och är mycket kall om vintern."
        cues, srt, _, report = c.build(timed(text, wps=2.5), dict(CFG, max_duration=4.0), "sv")
        self.assertTrue(report["wording_preserved"])
        for x in cues[:-1]:
            last = c._bare(x["text"].split()[-1])
            self.assertFalse(last.islower() and len(last) <= 2, [y["text"] for y in cues])

    def test_wrap_avoids_glue_line_break(self):
        lines = c.wrap("in the Western Hemisphere has a ruler-straight line cut right through it.", 2, 84)
        self.assertFalse(lines[0].endswith(" a"), lines)
        self.assertFalse(lines[0].endswith("Western"), lines)


class Formats(unittest.TestCase):
    def setUp(self):
        self.cues, self.srt, self.vtt, _ = c.build(timed(TEXT), CFG)

    def test_srt_valid_and_round_trips(self):
        blocks = self.srt.strip().split("\n\n")
        self.assertEqual(len(blocks), len(self.cues))
        for i, b in enumerate(blocks, 1):
            lines = b.split("\n")
            self.assertEqual(lines[0], str(i))
            self.assertRegex(lines[1], r"^\d\d:\d\d:\d\d,\d{3} --> \d\d:\d\d:\d\d,\d{3}$")
            self.assertLessEqual(len(lines) - 2, CFG["max_lines"])
        parsed = c.parse_srt(self.srt)
        self.assertEqual(" ".join(p["text"] for p in parsed), TEXT)
        self.assertEqual([(p["start_ms"], p["end_ms"]) for p in parsed],
                         [(x["start_ms"], x["end_ms"]) for x in self.cues])

    def test_vtt_valid(self):
        self.assertTrue(self.vtt.startswith("WEBVTT\n\n"))
        stamps = re.findall(r"^(\d\d:\d\d:\d\d\.\d{3}) --> (\d\d:\d\d:\d\d\.\d{3})$", self.vtt, re.M)
        self.assertEqual(len(stamps), len(self.cues))
        self.assertNotIn(",", "".join(s for pair in stamps for s in pair))

    def test_vtt_escapes_markup(self):
        words = timed("Use <b> & enjoy.")
        _, srt, vtt, _ = c.build(words, CFG)
        self.assertIn("&lt;b&gt; &amp; enjoy.", vtt)
        self.assertIn("<b> & enjoy.", srt)

    def test_timestamp_format_hours(self):
        self.assertEqual(c.ts(3723004, ","), "01:02:03,004")
        self.assertEqual(c.ts(0, "."), "00:00:00.000")


class Inputs(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)

    def write(self, name, obj):
        p = os.path.join(self.dir, name)
        with open(p, "w") as f: json.dump(obj, f)
        return p

    def voice_meta(self, words, timing=True):
        return self.write("narration.voice.json", {"schema": "yt-voice/1", "language": "en",
                          "timing": {"source": "provider"} if timing else None, "words": words if timing else []})

    def test_cli_from_voice_writes_all_files(self):
        out = os.path.join(self.dir, "captions"); os.mkdir(out)
        code, d = run(["--voice", self.voice_meta(timed(TEXT)), "--out-dir", out])
        self.assertEqual((code, d["status"]), (0, "ok"), d)
        self.assertEqual(sorted(os.listdir(out)), ["captions.json", "captions.srt", "captions.vtt"])
        meta = json.load(open(os.path.join(out, "captions.json")))
        self.assertEqual((meta["schema"], meta["language"]), ("yt-captions/1", "en"))
        self.assertTrue(meta["validation"]["wording_preserved"])
        code, d = run(["--voice", os.path.join(self.dir, "narration.voice.json"), "--out-dir", out])
        self.assertEqual((code, d["status"]), (2, "exists"))

    def test_voice_without_timing_refused(self):
        code, d = run(["--voice", self.voice_meta([], timing=False), "--out-dir", self.dir])
        self.assertEqual((code, d["status"]), (2, "no_timing"))
        self.assertEqual(sorted(os.listdir(self.dir)), ["narration.voice.json"])

    def test_generic_words_and_language(self):
        p = self.write("w.json", {"language": "sv", "words": timed("Hej och välkommen hit.")})
        code, d = run(["--words", p, "--out-dir", self.dir])
        self.assertEqual((code, d["language"]), (0, "sv"))
        self.assertIn("välkommen", open(os.path.join(self.dir, "captions.srt"), encoding="utf-8").read())

    def test_bad_inputs_are_json(self):
        bad_words = [
            [{"text": "a", "start": 1, "end": 0.5}],
            [{"text": "a", "start": 1, "end": 2}, {"text": "b", "start": 0.5, "end": 3}],
            [{"text": "two words", "start": 0, "end": 1}],
            [{"text": "x", "start": "0", "end": 1}],
            [{"text": "-->", "start": 0, "end": 1}],
            [],
        ]
        for words in bad_words:
            code, d = run(["--words", self.write("b.json", words), "--out-dir", self.dir])
            self.assertEqual(code, 2, words); self.assertIn("error", d)
        for argv in (["--words", "missing.json", "--out-dir", self.dir],
                     ["--words", self.write("ok.json", timed("hi there")), "--out-dir", self.dir, "--max-chars", "x"],
                     ["--words", os.path.join(self.dir, "ok.json"), "--out-dir", self.dir, "--language", "english!"],
                     ["--words", os.path.join(self.dir, "ok.json")],
                     ["--words", os.path.join(self.dir, "ok.json"), "--out-dir", self.dir, "stray"]):
            code, d = run(argv)
            self.assertEqual((code, "error" in d), (2, True), argv)

    def test_not_a_voice_file(self):
        code, d = run(["--voice", self.write("x.json", {"words": []}), "--out-dir", self.dir])
        self.assertEqual(code, 2); self.assertIn("yt-voice", d["error"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
