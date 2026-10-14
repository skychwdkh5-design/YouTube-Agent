#!/usr/bin/env python3
"""Safety tests: the protections must hold against alternative commands, scripts and paths - not only the obvious one.
No network, no credentials, nothing paid. Each case is a way someone (or a hurried agent) could plausibly try to get around a rule."""
import json, os, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "memory"))
import guard, protected, stop_check  # noqa: E402

B = "feature"          # the branch the tests pretend to be on


def blocked(cmd, branch=B): return guard.check_bash(cmd, branch) is not None


class PaidTts(unittest.TestCase):
    def test_every_way_of_running_the_paid_script_is_blocked(self):
        for c in ("python3 .claude/skills/yt-voice/voice.py --script s.md --output n.wav --confirm",
                  "cd .claude/skills/yt-voice && python3 voice.py --text hi --output n.wav --confirm",
                  "python voice.py --confirm --text hi --output n.wav",
                  "env YT_VOICE_AUTH=proxy python3 ./voice.py --text hi --output n.wav --confirm",
                  "sh -c 'python3 voice.py --text hi --output n.wav --confirm'",
                  "bash -lc \"cd x; python3 /abs/path/voice.py --text hi --output o.wav --confirm\"",
                  "nohup python3.13 voice.py --text hi --output o.wav --confirm &",
                  "echo go | xargs python3 voice.py --confirm --output o.wav --text hi"):
            self.assertTrue(blocked(c), c)

    def test_planning_and_the_orbital_path_are_allowed(self):
        self.assertFalse(blocked("python3 .claude/skills/yt-voice/voice.py --script s.md --output n.wav"))
        self.assertFalse(blocked("python3 tools/autopilot/orbital.py run ep003-x --stage tts --confirm"))

    def test_mentioning_the_script_in_text_is_not_a_command(self):
        self.assertFalse(blocked("echo 'never run voice.py --confirm directly' > notes.txt"))
        self.assertFalse(blocked("git commit -m 'document voice.py --confirm policy'"))
        self.assertFalse(blocked("grep -n -- --confirm .claude/skills/yt-voice/voice.py"))

    def test_direct_provider_calls_are_blocked(self):
        for c in ("curl -s -X POST https://api.elevenlabs.io/v1/text-to-speech/abc -d '{}'",
                  "wget --post-data=x https://api.elevenlabs.io/v1/sound-generation",
                  "python3 -c \"import urllib.request as u; u.urlopen('https://api.elevenlabs.io/v1/text-to-speech/x')\"",
                  "python3 -c 'import requests; requests.post(\"https://api.elevenlabs.io/v1/music\")'",
                  "node -e \"fetch('https://api.elevenlabs.io/v1/speech-to-speech/x')\""):
            self.assertTrue(blocked(c), c)
        self.assertFalse(blocked("curl -s https://api.elevenlabs.io/v1/voices/pNInz6obpgDQGcFmaJgB"), "a free read must stay possible")

    def test_new_scripts_cannot_embed_the_paid_endpoint(self):
        body = "import urllib.request\nurllib.request.urlopen('https://api.elevenlabs.io/v1/text-to-speech/x')\n"
        self.assertTrue(guard.check_edit("productions/ep003-x/tts_direct.py", body))
        self.assertIsNone(guard.check_edit(".claude/skills/yt-voice/voice.py", body), "the skill itself is where the gated call lives")
        self.assertIsNone(guard.check_edit("docs/notes.md", body))


class Git(unittest.TestCase):
    def test_pushing_to_main_in_any_spelling_is_blocked(self):
        for c in ("git push origin main", "git push origin HEAD:main", "git push origin HEAD:refs/heads/main", "git push -u origin feature:main",
                  "git push origin +HEAD:main", "git push --force origin main", "git push -f origin master", "git push --force-with-lease origin main",
                  "git -C . push origin main", "git -c user.name=x push origin HEAD:main", "git push --mirror origin", "git push --all origin",
                  "cd repo && git push origin main", "echo ok; git push origin main"):
            self.assertTrue(blocked(c), c)

    def test_branch_pushes_are_allowed(self):
        for c in ("git push -u origin autonomy/phase2", "git push origin feature", "git push origin HEAD:feature", "git push origin maintenance-fixes",
                  "git push --force-with-lease origin feature"):
            self.assertFalse(blocked(c), c)

    def test_bare_push_and_commit_on_main_are_blocked(self):
        self.assertTrue(blocked("git push", "main"))
        self.assertTrue(blocked("git push origin", "main"))
        self.assertTrue(blocked("git commit -m x", "main"))
        self.assertTrue(blocked("git merge feature", "main"))
        self.assertFalse(blocked("git commit -m x", "feature"))

    def test_github_tools_cannot_merge_or_write_main(self):
        self.assertTrue(guard.decide({"tool_name": "mcp__github__merge_pull_request", "tool_input": {"pullNumber": 17}}))
        self.assertTrue(guard.decide({"tool_name": "mcp__github__enable_pr_auto_merge", "tool_input": {}}))
        for tool in ("push_files", "create_or_update_file", "delete_file"):
            self.assertTrue(guard.decide({"tool_name": "mcp__github__" + tool, "tool_input": {"branch": "main", "path": "a"}}), tool)
            self.assertTrue(guard.decide({"tool_name": "mcp__github__" + tool, "tool_input": {"path": "a"}}), tool + " without a branch = default branch")
            self.assertIsNone(guard.decide({"tool_name": "mcp__github__" + tool, "tool_input": {"branch": "autonomy/x", "path": "a"}}))
        self.assertTrue(guard.decide({"tool_name": "mcp__github__push_files", "tool_input": {"branch": "x", "files": [{"path": "productions/dubai/final/ep002.srt"}]}}))
        self.assertIsNone(guard.decide({"tool_name": "mcp__github__create_pull_request", "tool_input": {}}))


class Publishing(unittest.TestCase):
    def test_uploads_are_blocked(self):
        for c in ("curl -X POST https://youtube.googleapis.com/upload/youtube/v3/videos?part=snippet -T final.mp4",
                  "python3 -c \"import requests; requests.post('https://www.googleapis.com/upload/youtube/v3/videos')\"",
                  "youtubeuploader -filename final.mp4", "youtube-upload final.mp4"):
            self.assertTrue(blocked(c), c)
        self.assertTrue(guard.decide({"tool_name": "mcp__youtube__upload_video", "tool_input": {}}))


class FinishedFiles(unittest.TestCase):
    P = "productions/dubai/final/ep002_final_v41.srt"

    def test_every_way_of_writing_to_a_finished_file_is_blocked(self):
        for c in (f"echo x > {self.P}", f"echo x >> {self.P}", f"rm {self.P}", f"mv {self.P} /tmp/x", f"cp /tmp/x {self.P}", f"sed -i 's/a/b/' {self.P}",
                  f"tee {self.P} < /tmp/x", f"truncate -s 0 {self.P}", f"git checkout -- {self.P}", f"git rm {self.P}", f"git restore {self.P}",
                  "sh -c 'echo x > productions/sahara-green/final/FINAL_REPORT.md'", "perl -pi -e 's/a/b/' productions/dubai/release/description.txt",
                  "rm -rf productions/dubai/final", "git clean -fd productions/dubai/release"):
            self.assertTrue(blocked(c), c)

    def test_reading_is_fine(self):
        for c in (f"cat {self.P}", f"head -5 {self.P}", f"git show HEAD:{self.P}", "ls productions/dubai/final", f"sha256sum {self.P}", f"cp {self.P} /tmp/copy.srt"):
            self.assertFalse(blocked(c), c)

    def test_file_tools_are_blocked(self):
        for tool in ("Edit", "Write", "MultiEdit"):
            self.assertTrue(guard.decide({"tool_name": tool, "tool_input": {"file_path": "/home/user/YouTube-Agent/" + self.P, "content": "x", "new_string": "x"}}), tool)


class Secrets(unittest.TestCase):
    def test_keys_never_reach_files(self):
        self.assertTrue(guard.check_edit("a.json", '{"k": "sk_' + "a" * 30 + '"}'))
        self.assertTrue(guard.check_edit("a.sh", "export TOKEN=ghp_" + "b" * 30))


class EffectReuse(unittest.TestCase):
    def test_a_new_file_that_duplicates_an_existing_effect_is_blocked(self):
        body = "def crossfade_filmstrip(frames):\n    return frames\n"
        msg = guard.check_edit("orbitalatlas/filmstrip_timeline.py", body, exists=False)
        self.assertIn("dubai_filmstrip_timeline_card", msg or "")
        msg = guard.check_edit("tools/new_radial_mask_reveal.py", "def run():\n    pass\n", exists=False)
        self.assertIn("oa_mask_reveal_geofocus_scalematch", msg or "")

    def test_editing_an_existing_file_tests_and_unrelated_files_are_fine(self):
        body = "def crossfade_filmstrip(frames):\n    return frames\n"
        self.assertIsNone(guard.check_edit("orbitalatlas/filmstrip_timeline.py", body, exists=True))
        self.assertIsNone(guard.check_edit("orbitalatlas/tests/test_filmstrip_timeline.py", body, exists=False))
        self.assertIsNone(guard.check_edit("tools/autopilot/new_report_helper.py", "def run():\n    pass\n", exists=False))
        self.assertIsNone(guard.check_edit("docs/filmstrip.md", body, exists=False))

    def test_a_justified_variant_is_allowed_with_the_marker(self):
        body = "# effect-reuse-checked: vertical filmstrip for Shorts, the Dubai one is horizontal\ndef filmstrip():\n    pass\n"
        self.assertIsNone(guard.check_edit("orbitalatlas/filmstrip_timeline.py", body, exists=False))

    def test_not_built_effects_do_not_block_work_on_them(self):
        # building a missing capability is allowed (the catalogue says it does not exist)
        self.assertIsNone(guard.check_edit("tools/music_mixer.py", "def mix():\n    pass\n", exists=False))


class Protected(unittest.TestCase):
    """protected.verify works on git content, so it holds whichever tool, script or path did the writing."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.r = self.tmp.name
        self.g("init", "-q", "-b", "release")
        os.makedirs(os.path.join(self.r, "productions", "dubai", "final"))
        with open(os.path.join(self.r, "productions", "dubai", "final", "a.txt"), "w") as f: f.write("final\n")
        with open(os.path.join(self.r, "keep.txt"), "w") as f: f.write("x\n")
        self.g("add", "-A"); self.g("commit", "-q", "-m", "release")
        self.g("branch", "work")
        self.g("checkout", "-q", "work")
        self.cfg = {"paths": ["productions/dubai/final/"], "release_refs": ["release", "origin/not-fetched"]}

    def g(self, *a):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", self.r, *a], capture_output=True, text=True)

    def test_untouched_passes_and_missing_refs_are_reported_not_failed(self):
        v = protected.verify(self.r, "HEAD", self.cfg)
        self.assertTrue(v["ok"]); self.assertEqual(v["checked_files"], 1); self.assertEqual(v["refs_not_in_this_clone"], ["origin/not-fetched"])

    def test_modified_file_is_caught_even_when_written_by_a_script(self):
        with open(os.path.join(self.r, "productions", "dubai", "final", "a.txt"), "w") as f: f.write("changed\n")     # any writer
        self.g("commit", "-qam", "innocent change")
        v = protected.verify(self.r, "HEAD", self.cfg)
        self.assertFalse(v["ok"]); self.assertEqual(v["violations"][0]["problem"], "modified")

    def test_deleted_file_is_caught(self):
        self.g("rm", "-q", "productions/dubai/final/a.txt")
        os.makedirs(os.path.join(self.r, "productions", "dubai", "final"), exist_ok=True)
        with open(os.path.join(self.r, "productions", "dubai", "final", "b.txt"), "w") as f: f.write("new\n")
        self.g("add", "-A"); self.g("commit", "-qm", "swap")
        v = protected.verify(self.r, "HEAD", self.cfg)
        self.assertFalse(v["ok"]); self.assertEqual(v["violations"][0]["problem"], "deleted")

    def test_adding_new_files_is_fine(self):
        with open(os.path.join(self.r, "productions", "dubai", "final", "c.txt"), "w") as f: f.write("more\n")
        self.g("add", "-A"); self.g("commit", "-qm", "add")
        self.assertTrue(protected.verify(self.r, "HEAD", self.cfg)["ok"])

    def test_a_branch_that_never_had_the_release_is_not_a_violation(self):
        self.g("checkout", "-q", "--orphan", "other"); self.g("rm", "-rfq", ".")
        with open(os.path.join(self.r, "x.txt"), "w") as f: f.write("x\n")
        self.g("add", "-A"); self.g("commit", "-qm", "other")
        self.assertTrue(protected.verify(self.r, "HEAD", self.cfg)["ok"])

    def test_the_real_repository_passes(self):
        v = protected.verify()
        self.assertTrue(v["ok"], v["violations"])


class StopHook(unittest.TestCase):
    def test_a_fix_without_a_memory_entry_is_flagged_once(self):
        msg = stop_check.memory_reminder(["Fix label clamp near the frame edge"], ["orbitalatlas/camera.py", "orbitalatlas/tests/test_engine.py"])
        self.assertIn("knowledge/solutions.json", msg)

    def test_recorded_fixes_and_non_fixes_pass(self):
        self.assertIsNone(stop_check.memory_reminder(["Fix label clamp"], ["orbitalatlas/camera.py", "knowledge/solutions.json"]))
        self.assertIsNone(stop_check.memory_reminder(["Fix typo [memory: n/a]"], ["tools/x.py"]))
        self.assertIsNone(stop_check.memory_reminder(["Add storyboard generator"], ["tools/autopilot/storyboard.py"]))
        self.assertIsNone(stop_check.memory_reminder(["Fix wording"], ["docs/AUTOPILOT.md"]))

    def test_second_stop_is_never_blocked(self):
        p = subprocess.run([sys.executable, os.path.join(HERE, "stop_check.py")], input=json.dumps({"stop_hook_active": True}), capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)


class Wiring(unittest.TestCase):
    """The hooks must actually be configured - an unwired guard protects nothing."""

    def test_settings_register_every_hook(self):
        root = os.path.dirname(os.path.dirname(HERE))
        with open(os.path.join(root, ".claude", "settings.json")) as f: st = json.load(f)
        pre = json.dumps(st["hooks"]["PreToolUse"])
        for tool in ("Bash", "Edit", "Write", "MultiEdit", "mcp__github__"):
            self.assertIn(tool, pre)
        self.assertIn("guard.py", pre)
        self.assertIn("kb.py", json.dumps(st["hooks"]["SessionStart"]))
        self.assertIn("stop_check.py", json.dumps(st["hooks"]["Stop"]))

    def test_the_hook_process_itself_blocks_with_exit_2(self):
        call = {"tool_name": "Bash", "tool_input": {"command": "git push origin " + "ma" + "in"}}
        p = subprocess.run([sys.executable, os.path.join(HERE, "guard.py")], input=json.dumps(call), capture_output=True, text=True)
        self.assertEqual(p.returncode, 2); self.assertIn("[guard]", p.stderr)
        p = subprocess.run([sys.executable, os.path.join(HERE, "guard.py")], input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}}), capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)


if __name__ == "__main__":
    unittest.main()
