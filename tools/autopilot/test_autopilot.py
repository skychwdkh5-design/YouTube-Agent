#!/usr/bin/env python3
"""Offline tests for the autopilot: topic rules, gates, the paid-stage approval wall, bounded retries, the guard hook.
No network, no credentials, no paid request is ever made."""
import json, math, os, struct, sys, tempfile, unittest, wave

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gates, guard, orbital, topics  # noqa: E402


def write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(obj if isinstance(obj, str) else json.dumps(obj))


def cand(i, us=3, ev=4, sw=3, no=3, dk=3, intl=3, url=True):
    return {"id": i, "scores": {"us": us, "sweden": sw, "norway": no, "denmark": dk, "international": intl, "visual": 4,
                                "curiosity": 4, "evidence": ev, "satellite": 4, "monetization": 4},
            "evidence_urls": ["https://example.org/x"] if url else []}


class TopicRules(unittest.TestCase):
    def test_strong_us_topic_not_rejected_for_low_scandinavian_relevance(self):
        r = topics.rank([cand("us_strong", us=5, sw=1, no=1, dk=1), cand("nordic", us=3, sw=5, no=5, dk=5)])
        self.assertEqual(r[0]["id"], "us_strong")

    def test_missing_evidence_loses_whatever_the_other_scores(self):
        r = topics.rank([cand("flashy", us=5, intl=5, ev=1), cand("solid", us=3, ev=4)])
        self.assertEqual(r[0]["id"], "solid")
        self.assertTrue(r[1]["evidence_gate_failed"])
        r = topics.rank([cand("nourl", us=5, url=False), cand("solid", us=2, ev=3)])
        self.assertEqual(r[0]["id"], "solid")

    def test_near_tie_on_us_prefers_international_and_scandinavian_reach(self):
        r = topics.rank([cand("a", us=4, sw=1, no=1, dk=1, intl=2), cand("b", us=4, sw=4, no=4, dk=4, intl=5)])
        self.assertEqual(r[0]["id"], "b")

    def test_scores_are_validated(self):
        with self.assertRaises(ValueError):
            topics.rank([cand("bad", us=9)])

    def test_satellite_null_is_renormalised(self):
        c = cand("nosat"); c["scores"]["satellite"] = None
        self.assertAlmostEqual(topics.weighted(c["scores"]), 3.0 + 0.0, delta=1.5)  # just must not raise


class Gates(unittest.TestCase):
    def wav(self, d, silence_s, tone_s=1.0, rate=16000):
        p = os.path.join(d, "n.wav")
        with wave.open(p, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
            frames = [0] * int(rate * silence_s) + [int(8000 * math.sin(2 * math.pi * 220 * i / rate)) for i in range(int(rate * tone_s))]
            w.writeframes(struct.pack("<%dh" % len(frames), *frames))
        return p

    def test_voice_onset_is_measured_on_the_narration_track(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertAlmostEqual(gates.voice_onset(self.wav(d, 3.35)), 3.35, delta=0.03)   # EP002 v1-v3 failure mode

    def test_late_voice_fails_the_tts_gate(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "voice")); self.wav(os.path.join(d, "voice"), 3.35)
            os.replace(os.path.join(d, "voice", "n.wav"), os.path.join(d, "voice", "narration.wav"))
            write(os.path.join(d, "voice", "narration.voice.json"), {"timing": {"level": "word"}, "words": [{"text": "a", "start": 3.4, "end": 3.6}]})
            g = gates.tts(d)
            self.assertFalse(g["ok"]); self.assertIn("voice starts", g["problems"][0])

    def test_chapters_rules(self):
        self.assertEqual(gates.chapters_ok("0:00 Intro\n1:10 Part\n3:00 End"), [])
        self.assertTrue(gates.chapters_ok("0:05 Intro\n1:10 Part\n3:00 End"))
        self.assertTrue(gates.chapters_ok("0:00 Intro\n0:05 Part\n3:00 End"))
        self.assertTrue(gates.chapters_ok("0:00 Intro\n1:00 Part"))

    def test_agent_cannot_grant_user_approved(self):
        with tempfile.TemporaryDirectory() as d:
            r = {"level": "USER_APPROVED", "approved_by": "claude", "frames_reviewed": list(range(20)), "not_verified": ["audio not heard"],
                 "defects_none_found_reason": "x"}
            write(os.path.join(d, "qc", "review.json"), r)
            self.assertFalse(gates.review(d)["ok"])
            r.update(level="VISUALLY_REVIEWED", approved_by="claude")
            write(os.path.join(d, "qc", "review.json"), r)
            self.assertTrue(gates.review(d)["ok"])
            r["frames_reviewed"] = [1, 2]
            write(os.path.join(d, "qc", "review.json"), r)
            self.assertFalse(gates.review(d)["ok"])

    def test_qc_pass_is_only_technically_valid(self):
        with tempfile.TemporaryDirectory() as d:
            write(os.path.join(d, "qc", "qc.json"), {"result": "PASS"})
            g = gates.qc(d)
            self.assertTrue(g["ok"]); self.assertIn("not a visual review", g["notes"][0])

    def test_claims_must_be_verified_and_sourced(self):
        with tempfile.TemporaryDirectory() as d:
            write(os.path.join(d, "story", "claims.json"), {"claims": [{"id": "C1", "text": "t", "status": "PENDING", "source_url": "https://a.b", "evidence_type": "model"}]})
            self.assertFalse(gates.claims(d)["ok"])
            write(os.path.join(d, "story", "claims.json"), {"claims": [{"id": "C1", "text": "t", "status": "VERIFIED", "source_url": "https://a.b", "evidence_type": "model"}]})
            self.assertTrue(gates.claims(d)["ok"])

    def test_package_requires_published_false(self):
        with tempfile.TemporaryDirectory() as d:
            for f, c in (("description.txt", "d"), ("chapters.txt", "0:00 A\n1:00 B\n2:00 C"), ("tags.txt", "a,b"), ("COPYRIGHT_CHECK.md", "x")):
                write(os.path.join(d, "release", f), c)
            write(os.path.join(d, "release", "metadata.json"), {"title": "T", "published": True})
            self.assertFalse(gates.package(d)["ok"])
            write(os.path.join(d, "release", "metadata.json"), {"title": "T", "published": False})
            self.assertTrue(gates.package(d)["ok"])


class Pipeline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["ORBITAL_PRODUCTIONS"] = self.tmp.name
        orbital.init("ep999-test")
        self.d = orbital.pdir("ep999-test")

    def tearDown(self):
        os.environ.pop("ORBITAL_PRODUCTIONS", None); self.tmp.cleanup()

    def script(self, text):
        write(os.path.join(self.d, "script.md"), text)

    def prime(self, text="One short line of narration."):
        """research + claims + locked script + tts plan: everything upstream of the paid stage."""
        write(os.path.join(self.d, "research", "candidates.json"), {"candidates": [cand("a"), cand("b"), cand("c")]})
        write(os.path.join(self.d, "research", "topic_decision.json"),
              {"chosen_id": "a", "reason": "r", "evidence_urls": ["https://example.org/a"], "us_hook": "h"})
        write(os.path.join(self.d, "story", "claims.json"),
              {"claims": [{"id": "C1", "text": "t", "status": "VERIFIED", "source_url": "https://a.b", "evidence_type": "model"}]})
        self.script(text)
        orbital.lock("ep999-test")
        orbital.run("ep999-test", "tts_plan")

    def stage(self, sid):
        return next(r for r in orbital.status("ep999-test")["stages"] if r["stage"] == sid)

    def test_fresh_production_starts_at_research_and_blocks_the_rest(self):
        s = orbital.status("ep999-test")
        self.assertEqual(s["next"]["stage"], "research")
        self.assertEqual(self.stage("research")["state"], "agent_todo")
        self.assertEqual(self.stage("tts")["state"], "blocked")

    def test_there_is_no_publish_stage(self):
        self.assertFalse([s for s in orbital.STAGES if "publish" in s or "upload" in s])
        with self.assertRaises(ValueError):
            orbital.approve("ep999-test", "publish", 0, "yes")

    def test_tts_plan_caps_chunks_and_flags_blank_line_cost(self):
        para = ("This is a sentence about a lake. " * 20).strip()
        self.script("\n\n".join([para] * 6))
        p = orbital.make_tts_plan("ep999-test")
        self.assertLessEqual(p["chunk_chars_max"], 1700)
        self.assertGreater(p["blank_line_chars"], 0)
        self.assertEqual(p["cache_dir"], "voice/cache")

    def test_paid_stage_without_owner_approval_sends_nothing(self):
        self.prime()
        r = orbital.run("ep999-test", "tts", confirm=True)
        self.assertFalse(r["ok"]); self.assertIn("no owner approval", r["error"])
        self.assertFalse(os.path.exists(os.path.join(self.d, "ledger.json")))

    def test_paid_stage_with_approval_still_needs_confirm_and_budget(self):
        self.prime()
        orbital.approve("ep999-test", "tts", 500, "ok, spend up to 500 credits")
        r = orbital.run("ep999-test", "tts", confirm=False)
        self.assertIn("--confirm", r["error"])
        orbital.approve("ep999-test", "tts", 5, "ok, spend up to 5 credits")      # budget smaller than the plan
        r = orbital.run("ep999-test", "tts", confirm=True)
        self.assertEqual(r["blocked_by"], ["tts_plan"])
        self.assertIn("exceed the approved", " ".join(self.stage("tts_plan")["gate"]["problems"]))
        self.assertFalse(os.path.exists(os.path.join(self.d, "ledger.json")))

    def test_script_change_after_plan_blocks_the_paid_call(self):
        self.prime("First text.")
        orbital.approve("ep999-test", "tts", 500, "yes, go ahead")
        self.script("Edited text after approval.")
        r = orbital.run("ep999-test", "tts", confirm=True)
        self.assertFalse(r["ok"]); self.assertEqual(r["blocked_by"], ["tts_plan"])
        self.assertEqual(self.stage("tts_plan")["blocked_by"], ["script"])
        self.assertIn("no longer matches", " ".join(self.stage("script")["gate"]["problems"]))
        self.assertFalse(os.path.exists(os.path.join(self.d, "ledger.json")))

    def test_approval_needs_the_owners_words(self):
        with self.assertRaises(ValueError):
            orbital.approve("ep999-test", "tts", 100, "")

    def test_free_stage_retries_transient_failures_at_most_twice(self):
        orbital.LIMITS["retry_backoff_s"] = [0, 0, 0]
        cmd = [sys.executable, "-c", "import sys; print('HTTP 502 gateway', file=sys.stderr); sys.exit(1)"]
        r = orbital.execute(cmd, self.d, retryable=True)
        self.assertFalse(r["ok"]); self.assertEqual(len(r["attempts"]), 2)

    def test_non_transient_failure_and_paid_stages_are_not_retried(self):
        orbital.LIMITS["retry_backoff_s"] = [0, 0, 0]
        r = orbital.execute([sys.executable, "-c", "import sys; print('bad timeline', file=sys.stderr); sys.exit(1)"], self.d, retryable=True)
        self.assertEqual(len(r["attempts"]), 1)
        r = orbital.execute([sys.executable, "-c", "import sys; print('HTTP 502', file=sys.stderr); sys.exit(1)"], self.d, retryable=False)
        self.assertEqual(len(r["attempts"]), 1)

    def test_failure_is_diagnosed_against_the_registry(self):
        orbital.LIMITS["retry_backoff_s"] = [0, 0, 0]
        r = orbital.execute([sys.executable, "-c", "import sys; print(\"ValueError: box offset can't be negative\", file=sys.stderr); sys.exit(1)"], self.d, retryable=False)
        self.assertTrue(any(x["id"] == "crop-box-leaves-source" for x in r["diagnosis"]), r["diagnosis"])

    def test_captions_stage_command_runs_the_real_skill_and_passes_its_gate(self):
        words = "The lake lost half of its water. Satellites saw it happen.".split()
        w, t = [], 0.2
        for x in words:
            w.append({"text": x, "start": round(t, 3), "end": round(t + 0.3, 3)}); t += 0.34
        write(os.path.join(self.d, "voice", "narration.voice.json"),
              {"schema": "yt-voice/1", "audio": "narration.wav", "duration": t + 0.2, "text": " ".join(words), "language": "en",
               "timing": {"source": "provider", "level": "word"}, "words": w, "characters": len(" ".join(words))})
        r = orbital.execute(orbital.stage_command("captions", self.d), self.d, retryable=True)
        self.assertTrue(r["ok"], r)
        self.assertTrue(gates.captions(self.d)["ok"])

    def test_research_gate_then_status_moves_on(self):
        c = {"candidates": [cand("a"), cand("b"), cand("c")]}
        write(os.path.join(self.d, "research", "candidates.json"), c)
        write(os.path.join(self.d, "research", "topic_decision.json"),
              {"chosen_id": "a", "reason": "r", "evidence_urls": ["https://example.org/a"], "us_hook": "h"})
        self.assertEqual(self.stage("research")["state"], "done")
        self.assertEqual(orbital.status("ep999-test")["next"]["stage"], "claims")

    def test_changed_upstream_output_marks_the_stage_stale(self):
        c = {"candidates": [cand("a"), cand("b"), cand("c")]}
        write(os.path.join(self.d, "research", "candidates.json"), c)
        write(os.path.join(self.d, "research", "topic_decision.json"),
              {"chosen_id": "a", "reason": "r", "evidence_urls": ["https://example.org/a"], "us_hook": "h"})
        write(os.path.join(self.d, "story", "claims.json"),
              {"claims": [{"id": "C1", "text": "t", "status": "VERIFIED", "source_url": "https://a.b", "evidence_type": "model"}]})
        self.assertTrue(orbital.complete("ep999-test", "claims")["ok"])
        self.assertEqual(self.stage("claims")["state"], "done")
        with open(os.path.join(self.d, "research", "topic_decision.json")) as f: d = json.load(f)
        d["reason"] = "changed my mind"
        write(os.path.join(self.d, "research", "topic_decision.json"), d)
        self.assertEqual(self.stage("claims")["state"], "stale")


class Guard(unittest.TestCase):
    def test_direct_paid_tts_is_blocked_but_the_orbital_path_is_not(self):
        self.assertTrue(guard.check_bash("python3 .claude/skills/yt-voice/voice.py --script s.md --output n.wav --confirm", "x"))
        self.assertIsNone(guard.check_bash("python3 .claude/skills/yt-voice/voice.py --script s.md --output n.wav", "x"))
        self.assertIsNone(guard.check_bash("python3 tools/autopilot/orbital.py run ep003 --stage tts --confirm", "x"))

    def test_main_is_protected(self):
        for c in ("git push origin main", "git push origin HEAD:main", "git push --force origin main", "git push -f origin main"):
            self.assertTrue(guard.check_bash(c, "feature"), c)
        self.assertTrue(guard.check_bash("git commit -m x", "main"))
        self.assertIsNone(guard.check_bash("git push -u origin autonomy/phase1-memory", "autonomy/phase1-memory"))
        self.assertIsNone(guard.check_bash("git commit -m x", "autonomy/phase1-memory"))

    def test_publishing_and_finished_files_are_protected(self):
        self.assertTrue(guard.check_bash("curl -X POST https://www.googleapis.com/upload/youtube/v3/videos"
                                         .replace("www.googleapis.com/upload/youtube", "youtube.googleapis.com/upload/youtube"), "x"))
        self.assertTrue(guard.check_edit("/home/user/YouTube-Agent/productions/dubai/final/ep002.srt"))
        self.assertTrue(guard.check_edit("productions/dubai/release/description.txt"))
        self.assertTrue(guard.check_edit("productions/sahara-green/final/FINAL_REPORT.md"))
        self.assertIsNone(guard.check_edit("productions/ep003-x/script.md"))

    def test_secrets_are_not_written(self):
        self.assertTrue(guard.check_edit("a.py", "KEY = 'sk_" + "a" * 32 + "'"))

    def test_decide_reads_a_tool_call(self):
        self.assertTrue(guard.decide({"tool_name": "Edit", "tool_input": {"file_path": "productions/dubai/final/x.json"}}))
        self.assertIsNone(guard.decide({"tool_name": "Read", "tool_input": {"file_path": "productions/dubai/final/x.json"}}))


if __name__ == "__main__":
    unittest.main()
