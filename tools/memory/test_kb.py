#!/usr/bin/env python3
"""Offline tests for the solutions registry tool."""
import copy, json, os, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kb  # noqa: E402

GOOD = {"id": "example-fix", "title": "Example fix", "status": "VERIFIED", "scope": "general", "area": "render", "date": "2026-10-14",
        "problem": "p", "root_cause": "c", "fix": "f", "reuse_when": "w", "verification": "v",
        "refs": {"code": ["tools/memory/kb.py"]}, "regression_test": "tools/memory/test_kb.py::KB.test_registry_is_valid"}


class KB(unittest.TestCase):
    def test_registry_is_valid(self):
        r = kb.validate()
        self.assertTrue(r["ok"], r["problems"])
        self.assertGreaterEqual(r["entries"], 30)

    def test_generated_view_is_current(self):
        with open(kb.VIEW, encoding="utf-8") as f: cur = f.read()
        self.assertEqual(cur, kb.render_md(), "run: python3 tools/memory/kb.py render")

    def test_every_entry_has_cause_fix_reuse_and_verification(self):
        for e in kb.load()["entries"]:
            for k in kb.REQUIRED: self.assertTrue(e.get(k), (e["id"], k))
            self.assertTrue(e.get("regression_test") or e.get("no_test_reason"), e["id"])

    def test_verified_without_test_or_reason_is_rejected(self):
        e = copy.deepcopy(GOOD); del e["regression_test"]
        errs, _ = kb.check_entry(e)
        self.assertTrue(any("regression_test or no_test_reason" in x for x in errs))
        e["no_test_reason"] = "needs real audio"
        self.assertEqual(kb.check_entry(e)[0], [])

    def test_dangling_references_are_rejected(self):
        e = copy.deepcopy(GOOD); e["refs"] = {"code": ["nope/missing.py"]}
        self.assertTrue(kb.check_entry(e)[0])
        e = copy.deepcopy(GOOD); e["regression_test"] = "tools/memory/test_kb.py::KB.test_does_not_exist"
        self.assertTrue(kb.check_entry(e)[0])

    def test_secrets_never_enter_the_registry(self):
        e = copy.deepcopy(GOOD); e["fix"] = "use key sk_" + "x" * 30
        self.assertTrue(any("secret" in x for x in kb.check_entry(e)[0]))

    def test_add_rejects_duplicates_and_accepts_new(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "s.json")
            with open(p, "w") as f: json.dump({"schema": "orbitalatlas-solutions/1", "entries": [copy.deepcopy(GOOD)]}, f)
            self.assertFalse(kb.add(copy.deepcopy(GOOD), p)["ok"])                       # same id
            twin = copy.deepcopy(GOOD); twin["id"] = "example-fix-again"
            r = kb.add(twin, p); self.assertFalse(r["ok"]); self.assertIn("duplicate", r["error"])
            new = copy.deepcopy(GOOD)
            new.update(id="other-thing", title="Completely different matter", problem="Unrelated words about audio loudness")
            self.assertTrue(kb.add(new, p)["ok"])
            self.assertEqual(len(kb.load(p)["entries"]), 2)

    def test_diagnose_and_search_find_known_problems(self):
        hits = kb.diagnose("HTTP Error 502: Bad Gateway while calling text-to-speech")
        self.assertTrue(any(h["id"] == "tts-gateway-502-chunk-size" for h in hits), hits)
        self.assertTrue(any(h["id"] == "tts-persistent-chunk-cache" for h in kb.search(["paid", "chunk", "failure", "cache"])))
        self.assertEqual(kb.diagnose("everything is fine"), [])

    def test_orbitalatlas_tests_run_as_modules_from_the_repo_root(self):
        cmd, cwd = kb.test_command("orbitalatlas/tests/test_engine.py")
        self.assertEqual(cmd[1:], ["-m", "unittest", "orbitalatlas.tests.test_engine"])
        self.assertEqual(cwd, kb.ROOT)
        cmd, cwd = kb.test_command("tools/memory/test_kb.py")
        self.assertEqual(cmd[1:], ["test_kb.py"])
        self.assertTrue(cwd.endswith(os.path.join("tools", "memory")))


if __name__ == "__main__":
    unittest.main()
