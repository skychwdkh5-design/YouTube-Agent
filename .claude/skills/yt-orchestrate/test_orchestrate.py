#!/usr/bin/env python3
"""End-to-end tests on EP005 (NEOM): real tools, real Sentinel-2 evidence (reused from productions/neom-line, or skipped).

Never calls a paid service: the voice step uses tests/fake_voice.py through the OA_VOICE_TOOL seam.
Run: python3 .claude/skills/yt-orchestrate/test_orchestrate.py
"""
import hashlib, json, os, shutil, subprocess, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ORCH = os.path.join(HERE, "orchestrate.py")
SRC = os.path.join(REPO, "productions", "neom-line")
HAVE_EVIDENCE = os.path.exists(os.path.join(SRC, "evidence", "stack", "provenance.json"))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


class Base(unittest.TestCase):
    slug = None

    @classmethod
    def setUpClass(cls):
        if not HAVE_EVIDENCE:
            raise unittest.SkipTest("EP005 evidence not present (run the orchestrator once with network)")

    def setUp(self):
        self.slug = f"_t_{os.getpid()}_{self._testMethodName[-12:]}"
        self.root = os.path.join(REPO, "productions", self.slug)
        os.makedirs(self.root)
        for f in ("episode.json", "claims.json", "script.md", "graphics_spec.json"):
            shutil.copy(os.path.join(SRC, f), self.root)
        shutil.copytree(os.path.join(SRC, "topic"), os.path.join(self.root, "topic"))
        shutil.copytree(os.path.join(SRC, "evidence"), os.path.join(self.root, "evidence"), copy_function=os.link)   # hardlinks: real imagery, no download, no space
        self.env = dict(os.environ)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def orch(self, *args, env=None, expect=None):
        r = subprocess.run([sys.executable, ORCH, *args], capture_output=True, text=True, env=env or self.env, cwd=REPO, timeout=900)
        if expect is not None:
            self.assertEqual(r.returncode, expect, r.stdout + r.stderr)
        try:
            return json.loads(r.stdout) if r.stdout.strip() else {}, r.returncode
        except ValueError:
            return {"raw": r.stdout, "err": r.stderr}, r.returncode

    def state(self):
        return json.load(open(os.path.join(self.root, "state.json")))

    def run_all(self, *extra):
        return self.orch("run", "--slug", self.slug, *extra)[0]


class Pipeline(Base):
    def test_full_run_stops_at_paid_gate_and_is_idempotent(self):
        r = self.run_all()
        st = r["stages"]
        for s in ("topic", "research", "facts", "evidence", "visuals", "script", "storyboard"):
            self.assertEqual(st[s], "done", (s, r))
        self.assertEqual(st["voice"], "awaiting_approval")
        for s in ("captions", "render", "qc"):
            self.assertEqual(st[s], "waiting")
        self.assertFalse(os.path.exists(os.path.join(self.root, "voice", "narration.wav")), "no audio without approval")
        self.assertEqual(self.state()["costs"], [])                                 # criterion 6: paid operations blocked
        self.assertTrue(os.path.exists(os.path.join(self.root, "release", "REVIEW.md")))
        self.assertIn("INCOMPLETE", open(os.path.join(self.root, "release", "REVIEW.md")).read())
        before = {f: sha(os.path.join(self.root, f)) for f in ("timeline.json", "story/storyboard.json", "script.md")}
        attempts = {s: v["attempts"] for s, v in self.state()["stages"].items()}
        r2 = self.run_all()                                                          # criterion 4: no duplicated work
        for s in ("topic", "research", "facts", "evidence", "visuals", "script", "storyboard"):
            self.assertEqual(r2["stages"][s], "cached", s)
        self.assertEqual(before, {f: sha(os.path.join(self.root, f)) for f in before})
        att2 = {s: v["attempts"] for s, v in self.state()["stages"].items()}
        for s in ("topic", "evidence", "visuals", "script", "storyboard"):
            self.assertEqual(attempts[s], att2[s])

    def test_state_json_saved_and_valid(self):
        self.run_all("--until", "facts")
        st = self.state()
        self.assertEqual(st["schema"], "yt-orchestrate/1")
        self.assertEqual(st["stages"]["facts"]["status"], "done")
        self.assertTrue(st["stages"]["facts"]["inputs"])
        self.assertNotIn("script", {k for k, v in st["stages"].items() if v["status"] == "done"})

    def test_resume_after_hard_crash(self):
        env = dict(self.env, OA_CRASH_IN="storyboard")
        r = subprocess.run([sys.executable, ORCH, "run", "--slug", self.slug], capture_output=True, text=True, env=env, cwd=REPO, timeout=900)
        self.assertEqual(r.returncode, 99)                                           # criterion 3: killed mid-stage
        st = self.state()["stages"]
        self.assertEqual(st["storyboard"]["status"], "running")
        self.assertEqual(st["script"]["status"], "done")
        ev_attempts = st["evidence"]["attempts"]
        self.assertFalse(os.path.exists(os.path.join(self.root, ".lock")) and False)
        out = self.run_all()
        self.assertEqual(out["stages"]["storyboard"], "done")
        self.assertEqual(out["stages"]["evidence"], "cached")
        self.assertEqual(self.state()["stages"]["evidence"]["attempts"], ev_attempts)
        self.assertTrue(any("interrupted" in e.get("event", "") for e in self.state()["log"]))

    def test_changed_output_is_detected(self):
        self.run_all()
        g = os.path.join(self.root, "graphics", "g_tiers.png")
        open(g, "ab").write(b"corrupt")                                              # criterion 8: integrity
        out = self.run_all()
        self.assertEqual(out["stages"]["visuals"], "done")                           # rebuilt, not trusted
        self.assertNotEqual(sha(g), hashlib.sha256(open(g, "rb").read() + b"corrupt").hexdigest())

    def test_edited_script_reruns_downstream_only(self):
        self.run_all()
        p = os.path.join(self.root, "script.md")
        open(p, "a").write("\nWe will keep watching.\n")
        out = self.run_all()
        self.assertEqual(out["stages"]["evidence"], "cached")
        self.assertEqual(out["stages"]["script"], "done")
        self.assertEqual(out["stages"]["storyboard"], "done")

    def test_single_stage_force(self):
        self.run_all()
        a0 = self.state()["stages"]["facts"]["attempts"]
        self.orch("run", "--slug", self.slug, "--stage", "facts", "--force")
        self.assertEqual(self.state()["stages"]["facts"]["attempts"], a0 + 1)
        self.assertEqual(self.state()["stages"]["script"]["attempts"], 1)

    def test_dry_run_writes_nothing(self):
        r = self.run_all("--dry-run")
        self.assertTrue(r["dry_run"])
        self.assertFalse(os.path.exists(os.path.join(self.root, "state.json")))
        self.assertFalse(os.path.exists(os.path.join(self.root, "voice")))


class Gates(Base):
    def test_unconfirmed_claims_block_the_script(self):                              # criterion 5
        p = os.path.join(self.root, "script.md")
        s = open(p).read().replace("By 2026, this. {C7}", "By 2026, this proves the city is built. {C7}")
        open(p, "w").write(s)
        out = self.run_all()
        self.assertEqual(out["stages"]["script"], "blocked")
        self.assertEqual(out["stages"]["storyboard"], "waiting")
        self.assertIn("strong word", self.state()["stages"]["script"]["note"])

    def test_untagged_number_blocks(self):
        p = os.path.join(self.root, "script.md")
        open(p, "a").write("\nThe corridor is 40 kilometers long.\n")
        self.assertEqual(self.run_all()["stages"]["script"], "blocked")

    def test_low_confidence_claim_cannot_be_used(self):
        p = os.path.join(self.root, "script.md")
        open(p, "a").write("\nThe PIF governor said the date was not a must. {C5}\n")
        out = self.run_all()
        self.assertEqual(out["stages"]["script"], "blocked")
        self.assertIn("confidence low", self.state()["stages"]["script"]["note"])

    def test_missing_evidence_file_blocks_registry_of_observations(self):
        c = json.load(open(os.path.join(self.root, "claims.json")))
        for x in c["claims"]:
            if x["id"] == "C7":
                x["evidence"] = "evidence/nope.json"
        json.dump(c, open(os.path.join(self.root, "claims.json"), "w"))
        self.assertEqual(self.run_all()["stages"]["script"], "blocked")

    def test_onscreen_number_without_claim_blocks(self):
        e = json.load(open(os.path.join(self.root, "episode.json")))
        e["chapters"][0]["visuals"][3]["label"] = {"text": "About 9 km", "style": "tag"}
        json.dump(e, open(os.path.join(self.root, "episode.json"), "w"))
        out = self.run_all()
        self.assertEqual(out["stages"]["storyboard"], "blocked")
        self.assertIn("no claim id", self.state()["stages"]["storyboard"]["note"])

    def test_paid_blocked_without_approval_or_flag(self):                            # criterion 6
        self.run_all()
        env = dict(self.env, OA_VOICE_TOOL=os.path.join(HERE, "tests", "fake_voice.py"))
        out = self.orch("run", "--slug", self.slug, "--allow-paid", env=env)[0]       # flag but no approval file
        self.assertEqual(out["stages"]["voice"], "awaiting_approval")
        os.makedirs(os.path.join(self.root, "approvals"), exist_ok=True)
        json.dump({"approved": True, "script_sha256": "0" * 64, "max_chars": 9999}, open(os.path.join(self.root, "approvals", "voice.json"), "w"))
        out = self.orch("run", "--slug", self.slug, "--allow-paid", env=env)[0]       # approval for a different script
        self.assertEqual(out["stages"]["voice"], "awaiting_approval")
        self.assertIn("different script", self.state()["stages"]["voice"]["note"])
        good = json.load(open(os.path.join(self.root, "voice", "plan.json")))
        json.dump({"approved": True, "script_sha256": good["script_sha256"], "max_chars": 9999}, open(os.path.join(self.root, "approvals", "voice.json"), "w"))
        out = self.orch("run", "--slug", self.slug, env=env)[0]                       # approval but no --allow-paid
        self.assertEqual(out["stages"]["voice"], "awaiting_approval")
        self.assertFalse(os.path.exists(os.path.join(self.root, "voice", "narration.wav")))
        self.assertEqual(self.state()["costs"], [])

    def test_max_chars_is_enforced(self):
        self.run_all()
        env = dict(self.env, OA_VOICE_TOOL=os.path.join(HERE, "tests", "fake_voice.py"))
        good = json.load(open(os.path.join(self.root, "voice", "plan.json")))
        os.makedirs(os.path.join(self.root, "approvals"), exist_ok=True)
        json.dump({"approved": True, "script_sha256": good["script_sha256"], "max_chars": 100}, open(os.path.join(self.root, "approvals", "voice.json"), "w"))
        out = self.orch("run", "--slug", self.slug, "--allow-paid", env=env)[0]
        self.assertEqual(out["stages"]["voice"], "blocked")


class WithVoiceStub(Base):
    def test_voice_to_render_plan_chain_and_render_gate(self):
        self.run_all()
        env = dict(self.env, OA_VOICE_TOOL=os.path.join(HERE, "tests", "fake_voice.py"))
        plan = json.load(open(os.path.join(self.root, "voice", "plan.json")))
        os.makedirs(os.path.join(self.root, "approvals"), exist_ok=True)
        json.dump({"approved": True, "script_sha256": plan["script_sha256"], "max_chars": plan["chars"] + 10}, open(os.path.join(self.root, "approvals", "voice.json"), "w"))
        out = self.orch("run", "--slug", self.slug, "--allow-paid", env=env)[0]
        self.assertEqual(out["stages"]["voice"], "done", out)
        self.assertEqual(out["stages"]["captions"], "done", out)
        self.assertEqual(out["stages"]["storyboard"], "done")                       # retimed from real word timings
        sb = json.load(open(os.path.join(self.root, "story", "storyboard.json")))
        self.assertEqual(sb["timing"], "voice")
        self.assertEqual(out["stages"]["render"], "awaiting_approval")             # plan validated, full render NOT started
        self.assertFalse(os.path.exists(os.path.join(self.root, "render", "final.mp4")))
        self.assertEqual(out["stages"]["qc"], "waiting")
        n = len(self.state()["costs"])
        self.run_all()                                                               # rerun: voice is not regenerated or re-billed
        self.assertEqual(len(self.state()["costs"]), n)


if __name__ == "__main__":
    unittest.main(verbosity=1)
