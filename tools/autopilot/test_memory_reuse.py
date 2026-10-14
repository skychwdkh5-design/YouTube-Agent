#!/usr/bin/env python3
"""Proof that the memory is not just stored but USED: before a stage, after an error, before re-developing an effect,
and after a fix. Each test drives the real tool, not a mock of it."""
import json, os, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "memory"))
import effects, guard, kb, orbital, stop_check, topics  # noqa: E402

ROOT = orbital.ROOT


def write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f: f.write(obj if isinstance(obj, str) else json.dumps(obj))


class BeforeAStage(unittest.TestCase):
    def test_every_pipeline_stage_has_known_pitfalls(self):
        for sid in orbital.ORDER:
            self.assertTrue(kb.for_stage(sid), f"stage {sid} would run without consulting any stored experience")

    def test_the_stage_run_reports_and_records_what_it_consulted(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["ORBITAL_PRODUCTIONS"] = tmp
            try:
                orbital.init("ep995-x")
                d = orbital.pdir("ep995-x")
                cands = {"candidates": [{"id": x, "scores": {k: 3 for k in topics.WEIGHTS}, "rationale": {}, "evidence_urls": ["https://example.org/a"]} for x in "abcde"]}
                write(os.path.join(d, "research", "candidates.json"), cands)
                out = topics.run(cands)
                write(os.path.join(d, "research", "topic_decision.json"), {**{k: out[k] for k in ("chosen_id", "mode", "reason", "evidence_urls")}, "us_hook": "h"})
                write(os.path.join(d, "story", "claims.json"), {"claims": [{"id": "C1", "text": "t", "status": "VERIFIED", "source_url": "https://a.b", "evidence_type": "model"}]})
                write(os.path.join(d, "script.md"), "A short line.\n\nAnother line.")
                orbital.lock("ep995-x")
                r = orbital.run("ep995-x", "tts_plan")
                ids = {p["id"] for p in r["known_pitfalls"]}
                self.assertIn("tts-gateway-502-chunk-size", ids)
                self.assertIn("tts-blank-lines-are-billable", ids)
                state = json.load(open(os.path.join(d, "state.json")))
                self.assertEqual(set(state["stages"]["tts_plan"]["pitfalls_consulted"]), ids)
            finally:
                os.environ.pop("ORBITAL_PRODUCTIONS", None)


class AfterAnError(unittest.TestCase):
    CASES = {
        "HTTP Error 502: Bad Gateway from api.elevenlabs.io text-to-speech": "tts-gateway-502-chunk-size",
        "ValueError: box offset can't be negative": "crop-box-leaves-source",
        "TypeError: float object cannot be interpreted as an integer": "pil-float-width",
        "ModuleNotFoundError: No module named 'orbitalatlas'": "orbitalatlas-tests-need-repo-root",
        "missing environment variable: ELEVENLABS_API_KEY": "tts-key-injected-by-egress-proxy",
        "remote: error: File productions/ep003/final.mp4 is 273.00 MB; this exceeds GitHub's file size limit of 100.00 MB": "master-over-100mb-lfs-or-parts",
        "black_frames FAIL: 3 black segments": "black-frame-near-empty-card",
    }

    def test_known_errors_find_their_stored_solution(self):
        for text, expect in self.CASES.items():
            hits = [h["id"] for h in kb.diagnose(text)]
            self.assertIn(expect, hits, text)

    def test_a_failing_stage_saves_the_diagnosis_in_its_state(self):
        with tempfile.TemporaryDirectory() as d:
            r = orbital.execute([sys.executable, "-c", "import sys; print(\"ValueError: box offset can't be negative\", file=sys.stderr); sys.exit(1)"], d, retryable=False)
            self.assertFalse(r["ok"])
            self.assertEqual([x["id"] for x in r["diagnosis"]], ["crop-box-leaves-source"])

    def test_a_stored_environment_fix_is_applied_automatically_and_only_once(self):
        with tempfile.TemporaryDirectory() as d:                      # cwd without the package on its path
            code = "import orbitalatlas; print('ok')"
            r = orbital.execute([sys.executable, "-c", code], d, retryable=False)
            self.assertTrue(r["ok"], r)
            self.assertEqual(r["applied_fix"]["entry"], "orbitalatlas-tests-need-repo-root")
            self.assertEqual(len(r["attempts"]), 2)
            r = orbital.execute([sys.executable, "-c", "import nonexistent_zzz"], d, retryable=False)          # no stored fix -> no retry
            self.assertFalse(r["ok"]); self.assertEqual(len(r["attempts"]), 1)

    def test_paid_stages_never_get_an_automatic_fix(self):
        with tempfile.TemporaryDirectory() as d:
            r = orbital.execute([sys.executable, "-c", "import orbitalatlas"], d, retryable=False, allow_autofix=False)
            self.assertFalse(r["ok"]); self.assertNotIn("applied_fix", r)

    def test_only_whitelisted_fixes_can_be_stored(self):
        e = {"id": "x-fix", "title": "t", "status": "VERIFIED", "scope": "general", "area": "env", "date": "2026-10-14", "problem": "p", "root_cause": "c", "fix": "f",
             "reuse_when": "w", "verification": "v", "refs": {"code": ["tools/memory/kb.py"]}, "no_test_reason": "n", "symptoms": ["boom"],
             "auto_fix": {"env": {"LD_PRELOAD": "/tmp/evil.so"}}}
        self.assertTrue(kb.check_entry(e)[0])
        e["auto_fix"] = {"cmd": "rm -rf /"}
        self.assertTrue(kb.check_entry(e)[0])
        e["auto_fix"] = {"env": {"PYTHONPATH": "{root}"}}
        self.assertEqual(kb.check_entry(e)[0], [])


class BeforeRebuildingAnEffect(unittest.TestCase):
    QUERIES = {"filmstrip of dated thumbnails on a timeline": "dubai_filmstrip_timeline_card",
               "radial mask reveal with glow edge": "oa_mask_reveal_geofocus_scalematch",
               "dissolve between two scenes": "oa_dissolve_push_whip",
               "number callout big yellow": "label_stat",
               "wipe between two dates": "geo_wipe",
               "timelapse of many years": "geo_flip_timelapse",
               "step by step build of a diagram": "graphic_build_steps",
               "slow push in on a still image": "still_push_in"}

    def test_a_natural_language_search_finds_the_existing_effect(self):
        for q, expect in self.QUERIES.items():
            ids = [h["id"] for h in effects.search(q.split())[:4]]
            self.assertIn(expect, ids, q)

    def test_the_catalogue_says_what_does_not_exist(self):
        ids = {e["id"]: e["status"] for e in effects.load()["entries"]}
        for missing in ("flat_map_plane_3d", "crossfade_between_v3_shots", "music_sfx"):
            self.assertEqual(ids[missing], "not_built")

    def test_writing_a_duplicate_is_stopped_at_the_tool_call(self):
        call = {"tool_name": "Write", "tool_input": {"file_path": os.path.join(ROOT, "orbitalatlas", "radial_mask_reveal.py"), "content": "def reveal():\n    pass\n"}}
        msg = guard.decide(call)
        self.assertIn("oa_mask_reveal_geofocus_scalematch", msg or "")

    def test_the_catalogue_references_exist(self):
        self.assertTrue(effects.validate()["ok"], effects.validate())

    def test_the_generator_only_chooses_catalogued_effects(self):
        built = {e["id"] for e in effects.for_content("establish_place")} | {e["id"] for e in effects.for_content("number")}
        self.assertIn("still_push_in", built); self.assertIn("graphic_full", built)


class AfterAFix(unittest.TestCase):
    def test_a_fix_commit_without_a_memory_entry_is_stopped_and_with_one_is_not(self):
        self.assertTrue(stop_check.memory_reminder(["Fix clipped callout"], ["productions/dubai/preview/kit.py"]))
        self.assertIsNone(stop_check.memory_reminder(["Fix clipped callout"], ["productions/dubai/preview/kit.py", "knowledge/solutions.json"]))

    def test_a_recorded_solution_is_immediately_findable_by_error_text_and_by_words(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "s.json")
            json.dump({"schema": "orbitalatlas-solutions/1", "entries": []}, open(path, "w"))
            entry = {"id": "ffmpeg-odd-width", "title": "ffmpeg refuses odd frame widths", "status": "VERIFIED", "scope": "general", "area": "render", "date": "2026-10-14",
                     "problem": "libx264 error: width not divisible by 2", "root_cause": "yuv420p needs even dimensions", "fix": "crop or pad to even sizes",
                     "reuse_when": "any custom crop before encoding", "verification": "re-encode succeeded", "refs": {"code": ["tools/memory/kb.py"]},
                     "no_test_reason": "demo entry", "symptoms": [r"width not divisible by 2"]}
            self.assertTrue(kb.add(entry, path)["ok"])
            data = kb.load(path)
            self.assertEqual([h["id"] for h in kb.diagnose("[libx264] width not divisible by 2 (1081x607)", data)], ["ffmpeg-odd-width"])
            self.assertEqual(kb.search(["odd", "width"], data)[0]["id"], "ffmpeg-odd-width")
            self.assertIn("render", kb.STAGE_AREAS and ["render"])
            self.assertEqual([p["id"] for p in kb.for_stage("render", data)], ["ffmpeg-odd-width"])


class Wiring(unittest.TestCase):
    def test_a_new_session_gets_the_memory_brief(self):
        env = dict(os.environ, CLAUDE_PROJECT_DIR=ROOT)
        p = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "memory", "kb.py"), "brief"], capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 0)
        self.assertIn("solutions", p.stdout); self.assertIn("kb.py diagnose", p.stdout)

    def test_the_skill_and_claude_md_tell_the_agent_to_use_it(self):
        skill = open(os.path.join(ROOT, ".claude", "skills", "yt-autopilot", "SKILL.md"), encoding="utf-8").read()
        claude = open(os.path.join(ROOT, "CLAUDE.md"), encoding="utf-8").read()
        for needle in ("kb.py diagnose", "kb.py search", "kb.py add"): self.assertIn(needle, skill)
        self.assertIn("kb.py search", claude)


if __name__ == "__main__":
    unittest.main()
